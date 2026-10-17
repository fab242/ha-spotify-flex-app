/*
 * flex-eq - 6-band equalizer between go-librespot and OwnTone.
 *
 *   flex-eq IN_FIFO OUT_FIFO CONTROL_FILE
 *
 * Reads 44.1 kHz s16le stereo PCM from IN_FIFO, filters it and writes it to OUT_FIFO.
 * CONTROL_FILE holds one line "enabled g1 g2 g3 g4 g5 g6" (gains in dB, -12..12) and is
 * re-read whenever it changes - new settings fade in within a fraction of a second,
 * without interrupting playback. Bands (peaking filters, like the Spotify app):
 * 60 Hz, 150 Hz, 400 Hz, 1 kHz, 2.4 kHz, 15 kHz.
 *
 * Loudness: boosts are NOT paid for by turning everything down (that made voices quieter).
 * Only the part of the curve above ALLOW_DB is taken off; peaks that would still clip are
 * caught by a look-ahead peak limiter (5.8 ms) that lowers the gain just before the peak
 * and releases smoothly - transparent instead of distorting.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <math.h>
#include <signal.h>
#include <sys/ioctl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#define RATE 44100.0
#define NB 6
#define CH 2
#define FRAMES 512
#define STEP_DB 0.35      /* max gain change per block (~11.6 ms) -> smooth fades */
#define ALLOW_DB 6.0      /* only boost above this (peak of the whole curve) is taken off the input */
#define LA 256            /* limiter look-ahead in frames (5.8 ms) */
#define THR 0.944         /* limiter ceiling: -0.5 dBFS */

static const double FREQ[NB] = {60, 150, 400, 1000, 2400, 15000};
static const double Q[NB] = {0.8, 1.0, 1.0, 1.0, 1.0, 0.8};

typedef struct { double b0, b1, b2, a1, a2; } coef_t;
typedef struct { double z1, z2; } state_t;

static double target[NB], cur[NB];
static int enabled;
static coef_t co[NB];
static state_t st[CH][NB];
static double pre = 1.0;

static void design(int i, double g) {
    double A = pow(10.0, g / 40.0), w = 2.0 * M_PI * FREQ[i] / RATE;
    double cs = cos(w), sn = sin(w), alpha = sn / (2.0 * Q[i]);
    double b0, b1, b2, a0, a1, a2;
    if (0) {                            /* shelves (kept for reference, not used) */
        double sq = 2.0 * sqrt(A) * alpha;
        if (i == 0) {
            b0 = A * ((A + 1) - (A - 1) * cs + sq);
            b1 = 2 * A * ((A - 1) - (A + 1) * cs);
            b2 = A * ((A + 1) - (A - 1) * cs - sq);
            a0 = (A + 1) + (A - 1) * cs + sq;
            a1 = -2 * ((A - 1) + (A + 1) * cs);
            a2 = (A + 1) + (A - 1) * cs - sq;
        } else {
            b0 = A * ((A + 1) + (A - 1) * cs + sq);
            b1 = -2 * A * ((A - 1) + (A + 1) * cs);
            b2 = A * ((A + 1) + (A - 1) * cs - sq);
            a0 = (A + 1) - (A - 1) * cs + sq;
            a1 = 2 * ((A - 1) - (A + 1) * cs);
            a2 = (A + 1) - (A - 1) * cs - sq;
        }
    } else {                            /* peaking */
        b0 = 1 + alpha * A; b1 = -2 * cs; b2 = 1 - alpha * A;
        a0 = 1 + alpha / A; a1 = -2 * cs; a2 = 1 - alpha / A;
    }
    co[i] = (coef_t){b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0};
}

/* peak gain of the whole curve in dB (overlapping boosts add up) */
static double peak_db(void) {
    double peak = 0;
    for (int n = 0; n < 64; n++) {
        double w = 2.0 * M_PI * 20.0 * pow(1000.0, n / 63.0) / RATE;  /* 20 Hz .. 20 kHz */
        double c1 = cos(w), s1 = sin(w), c2 = cos(2 * w), s2 = sin(2 * w), mag = 1;
        for (int i = 0; i < NB; i++) {
            coef_t *k = &co[i];
            double nr = k->b0 + k->b1 * c1 + k->b2 * c2, ni = -(k->b1 * s1 + k->b2 * s2);
            double dr = 1 + k->a1 * c1 + k->a2 * c2, di = -(k->a1 * s1 + k->a2 * s2);
            mag *= sqrt((nr * nr + ni * ni) / (dr * dr + di * di));
        }
        double db = 20 * log10(mag);
        if (db > peak) peak = db;
    }
    return peak;
}

static void redesign(void) {
    for (int i = 0; i < NB; i++) design(i, cur[i]);
    double cut = peak_db() - ALLOW_DB;
    pre = cut > 0 ? pow(10.0, -cut / 20.0) : 1.0;
}

static int flat(void) {
    for (int i = 0; i < NB; i++)
        if (fabs(cur[i]) > 1e-6 || fabs(target[i]) > 1e-6) return 0;
    return 1;
}

static void read_control(const char *path) {
    static time_t mtime; static long nsec; static off_t size = -1;
    struct stat sb;
    if (stat(path, &sb) != 0) return;
    if (sb.st_mtim.tv_sec == mtime && sb.st_mtim.tv_nsec == nsec && sb.st_size == size) return;
    mtime = sb.st_mtim.tv_sec; nsec = sb.st_mtim.tv_nsec; size = sb.st_size;
    FILE *f = fopen(path, "r");
    if (!f) return;
    int en = 0; double g[NB] = {0};
    int n = fscanf(f, "%d %lf %lf %lf %lf %lf %lf", &en, &g[0], &g[1], &g[2], &g[3], &g[4], &g[5]);
    fclose(f);
    if (n != 1 + NB) return;
    enabled = en != 0;
    for (int i = 0; i < NB; i++) {
        double v = enabled ? g[i] : 0.0;
        target[i] = v > 12 ? 12 : v < -12 ? -12 : v;
    }
    fprintf(stderr, "[flex-eq] %s %.1f %.1f %.1f %.1f %.1f %.1f\n", enabled ? "on" : "off",
            target[0], target[1], target[2], target[3], target[4], target[5]);
}

static int step_gains(void) {
    int moved = 0;
    for (int i = 0; i < NB; i++) {
        double d = target[i] - cur[i];
        if (fabs(d) < 1e-9) continue;
        cur[i] += d > STEP_DB ? STEP_DB : d < -STEP_DB ? -STEP_DB : d;
        moved = 1;
    }
    return moved;
}

/* --- look-ahead limiter: delay line + sliding minimum of the required gain --- */
#define RING LA                         /* slot nfr % LA holds frame nfr - LA */
#define DQ (LA + 2)
static double dl[RING][CH];             /* delay line */
static long nfr;                         /* frames pushed so far */
static long dq_i[DQ]; static double dq_v[DQ]; static int dq_h, dq_n;
static double gs = 1.0;                  /* smoothed limiter gain */
static double a_att, a_rel;

static void limiter_reset(void) {
    memset(dl, 0, sizeof dl); nfr = 0; dq_h = dq_n = 0; gs = 1.0;
}

static void dq_push(long i, double v) {   /* monotonic deque: front = minimum of the window */
    while (dq_n && dq_v[(dq_h + dq_n - 1) % DQ] >= v) dq_n--;
    int at = (dq_h + dq_n) % DQ;
    dq_i[at] = i; dq_v[at] = v; dq_n++;
    while (dq_i[dq_h] < i - LA) { dq_h = (dq_h + 1) % DQ; dq_n--; }
}

/* Filters `frames` frames in place; output is the input delayed by LA frames. */
static void process(short *pcm, int frames, int eq_on) {
    for (int f = 0; f < frames; f++) {
        double x[CH], peak = 0;
        for (int c = 0; c < CH; c++) {
            double v = pcm[f * CH + c] / 32768.0;
            if (eq_on) {
                v *= pre;
                for (int i = 0; i < NB; i++) {
                    coef_t *k = &co[i]; state_t *s = &st[c][i];
                    double y = k->b0 * v + s->z1;
                    s->z1 = k->b1 * v - k->a1 * y + s->z2;
                    s->z2 = k->b2 * v - k->a2 * y;
                    v = y;
                }
            }
            x[c] = v;
            if (fabs(v) > peak) peak = fabs(v);
        }
        double need = (eq_on && peak > THR) ? THR / peak : 1.0;
        int w = (int)(nfr % RING);
        double out[CH];
        for (int c = 0; c < CH; c++) { out[c] = dl[w][c]; dl[w][c] = x[c]; }  /* slot w held frame nfr-LA */
        dq_push(nfr, need);
        nfr++;
        double wmin = dq_v[dq_h];
        gs += (wmin - gs) * (wmin < gs ? a_att : a_rel);
        if (gs > 0.999999) gs = 1.0;
        if (gs > wmin && wmin < 1.0 && dq_i[dq_h] == nfr - 1 - LA) gs = wmin;  /* never late at the peak */
        for (int c = 0; c < CH; c++) {
            double y = gs == 1.0 ? out[c] * 32768.0 : out[c] * gs * 32768.0;
            pcm[f * CH + c] = (short)lrint(y > 32767 ? 32767 : y < -32768 ? -32768 : y);
        }
    }
}

static double now(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1e9;
}

static int open_out(const char *path) {
    for (;;) {
        int fd = open(path, O_WRONLY);   /* blocks until OwnTone reads the pipe */
        if (fd >= 0) return fd;
        fprintf(stderr, "[flex-eq] cannot open %s: %s\n", path, strerror(errno));
        sleep(1);
    }
}

/* ---- Abzweig für die Liedtext-Analyse (optional, 4. Argument) ------------------------------
 * Rohes PCM vor dem Equalizer, als Nachrichten <= PIPE_BUF (atomar): "FXT2", uint32 Frames,
 * uint64 fortlaufender Frame-Zähler, uint32 Bytes, die beim Lesen dieses Blocks noch in der Pipe zu
 * OwnTone warteten (so weit liegt der Block hinter dem, was OwnTone gerade liest), dann die Samples.
 * Nicht-blockierend: liest niemand mit oder ist die Pipe voll, werden nur Analysedaten verworfen –
 * die Wiedergabe stockt nie. */
#define TAP_HEAD 20
#define TAP_MAX_FRAMES ((4096 - TAP_HEAD) / (CH * 2))
static const char *tap_path;
static int tap_fd = -1;
static double tap_retry;
static unsigned long long tap_frames;   /* Frames seit Start von flex-eq (auch ohne Leser gezählt) */

static void tap(const short *pcm, size_t frames, unsigned int queued) {
    if (!tap_path) return;
    if (tap_fd < 0) {
        double t = now();
        if (t >= tap_retry) {
            tap_fd = open(tap_path, O_WRONLY | O_NONBLOCK);   /* ENXIO, solange niemand liest */
            tap_retry = t + 1.0;
            if (tap_fd >= 0) fcntl(tap_fd, F_SETPIPE_SZ, 1 << 20);
        }
    }
    size_t done = 0;
    while (done < frames) {
        size_t n = frames - done;
        if (n > TAP_MAX_FRAMES) n = TAP_MAX_FRAMES;
        if (tap_fd >= 0) {
            static char msg[4096];
            unsigned int nf = (unsigned int)n;
            unsigned long long idx = tap_frames + done;
            memcpy(msg, "FXT2", 4);
            memcpy(msg + 4, &nf, 4);
            memcpy(msg + 8, &idx, 8);
            memcpy(msg + 16, &queued, 4);
            memcpy(msg + TAP_HEAD, pcm + done * CH, n * CH * 2);
            ssize_t w = write(tap_fd, msg, TAP_HEAD + n * CH * 2);
            if (w < 0 && errno != EAGAIN && errno != EINTR) { close(tap_fd); tap_fd = -1; }
        }
        done += n;
    }
    tap_frames += frames;
}

static int write_all(int fd, const char *buf, size_t len) {
    while (len) {
        ssize_t n = write(fd, buf, len);
        if (n < 0) { if (errno == EINTR) continue; return -1; }
        buf += n; len -= (size_t)n;
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 4 && argc != 5) { fprintf(stderr, "usage: flex-eq IN_FIFO OUT_FIFO CONTROL_FILE [TAP_FIFO]\n"); return 2; }
    if (argc == 5) tap_path = argv[4];
    signal(SIGPIPE, SIG_IGN);
    setvbuf(stderr, NULL, _IOLBF, 0);
    a_att = 1.0 - exp(-1.0 / (LA / 5.0));          /* reaches the target within the look-ahead */
    a_rel = 1.0 - exp(-1.0 / (0.25 * RATE));        /* 250 ms release */
    read_control(argv[3]);
    memcpy(cur, target, sizeof cur);
    redesign();
    static short pcm[FRAMES * CH + 2];   /* short-aligned buffer */
    char *buf = (char *)pcm;
    const size_t cap = FRAMES * CH * 2;
    int was_flat = 1;
    for (;;) {
        int in = open(argv[1], O_RDONLY);  /* blocks until go-librespot writes */
        if (in < 0) { fprintf(stderr, "[flex-eq] cannot open %s: %s\n", argv[1], strerror(errno)); sleep(1); continue; }
        fcntl(in, F_SETPIPE_SZ, 4096);      /* keep the extra buffering (= delay) tiny */
        int out = open_out(argv[2]);        /* mirror the writer: open/close with the input */
        memset(st, 0, sizeof st);
        limiter_reset();
        size_t have = 0;
        double checked = 0;
        for (;;) {
            ssize_t n = read(in, buf + have, cap - have);
            if (n < 0 && errno == EINTR) continue;
            if (n <= 0) break;              /* writer closed: wait for the next one */
            have += (size_t)n;
            size_t frames = have / (CH * 2);
            if (!frames) continue;
            double t = now();
            if (t - checked > 0.1) { read_control(argv[3]); checked = t; }
            if (step_gains()) redesign();
            int eq_on = !flat();
            if (!eq_on) was_flat = 1;
            else if (was_flat) { memset(st, 0, sizeof st); was_flat = 0; }
            if (tap_path) {                 /* vor dem Equalizer: unverändertes Audio */
                int queued = 0;
                if (ioctl(out, FIONREAD, &queued) < 0 || queued < 0) queued = 0;
                tap(pcm, frames, (unsigned int)queued);
            }
            process(pcm, (int)frames, eq_on);
            size_t bytes = frames * CH * 2;
            if (write_all(out, buf, bytes) < 0) {
                fprintf(stderr, "[flex-eq] output closed (%s) - reopening\n", strerror(errno));
                close(out);
                out = open_out(argv[2]);
            }
            memmove(buf, buf + bytes, have - bytes);
            have -= bytes;
        }
        /* flush the look-ahead so the end of the stream is not cut off */
        static short tail[LA * CH];
        memset(tail, 0, sizeof tail);
        process(tail, LA, !flat());
        write_all(out, (const char *)tail, sizeof tail);
        close(in);
        close(out);
    }
}
