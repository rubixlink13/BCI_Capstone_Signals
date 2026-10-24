import numpy as np
import matplotlib.pyplot as plt

def convert_csv_to_array(filepath, delimiter=",", skip_header=True, dtype=float):
    return np.genfromtxt(
        filepath,
        delimiter=delimiter,
        skip_header=1 if skip_header else 0,
        dtype=dtype,
    )

TIMEOUT_MS = 2.5  # no threshold crossed within this window -> timeout flag
QUIET_MS = 0.5    # quiet (refractory) interval: signal between N1 and P1 for longer than this -> timeout flag

# Error flag order: [dropped_event, fifo_overflow, invalid_seq, overlap, timeout, saturation]
FLAG_TIMEOUT = 4

def process_waveform(filepath, channel_id, thresholds, timeout_ms=TIMEOUT_MS, quiet_ms=QUIET_MS):
    waveform = convert_csv_to_array(filepath)
    flags = [0, 0, 0, 0, 0, 0]
    t_begin = waveform[0][0]  # timeout window is measured from the start of the capture

    # thresholds = [P1, P2, P3, P4, N1, N2, N3, N4]
    peak_count = 0
    trough_count = 0

    quiet_start = None  # timestamp at which the current quiet stretch began (None = not quiet)

    is_peak = False
    is_trough = False
    #spike_started = False

    event_start = -1

    time_to_peak = -1

    highest_peak = -1
    highest_trough = -1

    for t in waveform:
        # --- quiet interval: only tracked once an event has started (before that, the
        # --- 2.5 ms timeout below applies). Quiet = no threshold active, N1 < v < P1.
        if event_start >= 0:
            if thresholds[4] < t[1] < thresholds[0]:
                if quiet_start is None:
                    quiet_start = t[0]
                elif round(t[0] - quiet_start, 9) > quiet_ms:
                    flags[FLAG_TIMEOUT] = 1
            else:
                quiet_start = None

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

    # --- timeout: no threshold crossed within timeout_ms of the start of the capture ---
    capture_end = waveform[-1][0]
    if event_start < 0:
        # never crossed; only a timeout if we actually observed the full window
        if capture_end - t_begin >= timeout_ms:
            flags[FLAG_TIMEOUT] = 1
    elif event_start - t_begin > timeout_ms:
        flags[FLAG_TIMEOUT] = 1

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