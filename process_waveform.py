import numpy as np
import matplotlib.pyplot as plt

def convert_csv_to_array(filepath, delimiter=",", skip_header=True, dtype=float):
    return np.genfromtxt(
        filepath,
        delimiter=delimiter,
        skip_header=1 if skip_header else 0,
        dtype=dtype,
    )

TIMEOUT_MS = 2.5  # event timeout: no threshold crossed for this long between spikes -> timeout flag
QUIET_MS = 0.5    # quiet/refractory interval: max gap between the two phases of a biphasic pulse -> timeout flag

# Error flag order: [dropped_event, fifo_overflow, invalid_seq, overlap, timeout, saturation]
FLAG_TIMEOUT = 4

def process_waveform(filepath, channel_id, thresholds, timeout_ms=TIMEOUT_MS, quiet_ms=QUIET_MS):
    waveform = convert_csv_to_array(filepath)
    flags = [0, 0, 0, 0, 0, 0]

    # thresholds = [P1, P2, P3, P4, N1, N2, N3, N4]
    peak_count = 0
    trough_count = 0

    # Timeout tracking (flags only; independent of the peak/trough counting below).
    # quiet = no threshold active (N1 < v < P1). The allowed length of a quiet stretch depends on where we are:
    #   - waiting for first phase (start of capture, or after a completed pulse): timeout_ms (2.5 ms)
    #   - between phase 1 and phase 2 of a biphasic pulse: quiet_ms (0.5 ms)
    quiet_start = waveform[0][0]  # capture starts quiet; if the first sample is active this is reset below
    pulse_phase = 0               # 0 = waiting for a pulse, 1 = phase 1 seen, 2 = opposite phase reached (pulse complete)
    first_polarity = 0            # +1 / -1: polarity of phase 1

    is_peak = False
    is_trough = False
    #spike_started = False

    event_start = -1

    time_to_peak = -1

    highest_peak = -1
    highest_trough = -1

    for t in waveform:
        # --- timeout flag tracking ---
        v = t[1]
        if thresholds[4] < v < thresholds[0]:  # quiet: no threshold active
            if quiet_start is None:
                quiet_start = t[0]
                if pulse_phase == 2:         # phase 2 has ended -> pulse over, wait for the next one
                    pulse_phase = 0
            limit = quiet_ms if pulse_phase == 1 else timeout_ms
            if round(t[0] - quiet_start, 9) > limit:
                flags[FLAG_TIMEOUT] = 1
        else:
            quiet_start = None
            polarity = 1 if v >= thresholds[0] else -1
            if pulse_phase == 0:             # start of a new pulse
                pulse_phase = 1
                first_polarity = polarity
            elif polarity != first_polarity:  # opposite phase reached -> biphasic pulse complete
                pulse_phase = 2

        if not is_peak and not is_trough:
            if t[1] >= thresholds[peak_count] and peak_count < 4:
                peak_count += 1
                is_peak = True
                highest_peak = t[0]
                event_start = t[0]

            if t[1] <= thresholds[trough_count + 4] and trough_count < 4:
                trough_count += 1
                is_trough = True
                highest_trough = t[0]
                event_start = t[0]

        if is_peak and not is_trough:
            if peak_count < 4 and t[1] >= thresholds[peak_count]:
                peak_count += 1
                highest_peak = t[0]

            if trough_count == 0 and t[1] <= thresholds[trough_count + 4]:
                trough_count += 1
                is_peak = False
                is_trough = True
                highest_trough = t[0]

        if is_trough and not is_peak:
            if trough_count < 4 and t[1] <= thresholds[trough_count + 4]:
                trough_count += 1
                highest_trough = t[0]

            if peak_count == 0 and t[1] >= thresholds[peak_count]:
                peak_count += 1
                is_peak = True
                is_trough = False
                highest_peak = t[0]

    if event_start < 0:
        # no event at all: nothing meaningful to report for timing
        return channel_id, -1, 0, 0, -1, flags

    if peak_count > trough_count:
        time_to_peak = highest_peak - event_start
    elif peak_count < trough_count:
        time_to_peak = highest_trough - event_start
    else:
        time_to_peak = min(highest_peak, highest_trough) - event_start

    return channel_id, int(event_start * 1e3), peak_count, trough_count, int(time_to_peak * 1e3), flags

def plot_array(filepath):
    array = convert_csv_to_array(filepath)
    t_values = [t[0] for t in array]
    waveform = [t[1] for t in array]

    plt.figure(figsize=(10, 5))
    plt.plot(t_values, waveform, color='forestgreen', linewidth=2)

    # Styling and labels
    plt.title('Waveform', fontsize=13, fontweight='bold')
    plt.xlabel('Time (t)', fontsize=12)
    plt.ylabel('Amplitude', fontsize=12)
    plt.axhline(0, color='black', linestyle='--', linewidth=0.8, alpha=0.7)  # Baseline reference
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.xlim(0, max(t_values))
    plt.ylim(min(waveform) - 0.5, max(waveform) + 0.5)
    plt.legend(loc='upper right')

    plt.show()


        


if __name__ == '__main__':
    #print(convert_csv_to_array('positive_then_negative.csv'))
    print(process_waveform('large_spike.csv', 0, [50, 100, 200, 300, -50, -100, -200, -300]))
    #print(process_waveform('noisy.csv', 0, [50, 100, 200, 300, -50, -100, -200, -300]))
    #plot_array('small_spike.csv')