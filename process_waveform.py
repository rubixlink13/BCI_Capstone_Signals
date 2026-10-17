import numpy as np
import matplotlib.pyplot as plt

def convert_csv_to_array(filepath, delimiter=",", skip_header=True, dtype=float):
    return np.genfromtxt(
        filepath,
        delimiter=delimiter,
        skip_header=1 if skip_header else 0,
        dtype=dtype,
    )

def process_waveform(filepath, channel_id, thresholds):
    waveform = convert_csv_to_array(filepath)

    # thresholds = [P1, P2, P3, P4, N1, N2, N3, N4]
    peak_count = 0
    trough_count = 0

    quiet_time = 0

    is_peak = False
    is_trough = False
    #spike_started = False

    event_start = -1

    time_to_peak = -1

    highest_peak = -1
    highest_trough = -1

    for t in waveform:
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

    if peak_count > trough_count:
        time_to_peak = highest_peak - event_start
    elif peak_count < trough_count:
        time_to_peak = highest_trough - event_start
    else:
        time_to_peak = min(highest_peak, highest_trough) - event_start

    return channel_id, int(event_start * 1e3), peak_count, trough_count, int(time_to_peak * 1e3)

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
    #print(process_waveform('noisy.csv', 0, [50, 100, 200, 300, -50, -100, -200, -300]))
    plot_array('small_spike.csv')