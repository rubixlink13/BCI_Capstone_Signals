import numpy as np
import matplotlib.pyplot as plt
import random

def generate_waveform(sample_rate, A1, A2, rise1, fall1, rise2, fall2, T, offset, noise, noise_seed, waveform_type, test_case):
    """
    Generates a biphasic waveform with independent rise and fall times for both phases.
    
    Each phase is constructed from two quarter-sine waves squared stitched together at the peak/trough.

    The time array is built internally from sample_rate and duration.

    Returns: t, waveform, sample_rate, and metadata
    """
    # 0. Build the time array from sample_rate and duration
    t = np.arange(0, T, 1.0 / (sample_rate/1000))
    
    # 1. Apply the horizontal offset shift
    shifted_t = t - offset
    
    # 2. Take the modulus of the shifted time for periodicity
    mod_t = np.mod(shifted_t, T)
    
    # 3. Initialize the output array with zeros
    y = np.zeros_like(t)
    
    # 4. Calculate absolute time boundaries for the pieces
    t0 = 0.0
    t1 = rise1
    t2 = rise1 + fall1
    t3 = rise1 + fall1 + rise2
    t4 = rise1 + fall1 + rise2 + fall2
    
    # 5. Create boolean masks for each segment
    p1_rise = (mod_t >= t0) & (mod_t < t1)
    p1_fall = (mod_t >= t1) & (mod_t < t2)
    p2_rise = (mod_t >= t2) & (mod_t < t3)
    p2_fall = (mod_t >= t3) & (mod_t < t4)
    
    # 6. Apply formulas (using quarter-sine transformations)
    # Phase 1 - Rise (0 to spike1 over rise1)
    y[p1_rise] = A1 * np.sin((np.pi / 2) * (mod_t[p1_rise] / rise1))**2
    
    # Phase 1 - Fall (spike1 to 0 over fall1)
    y[p1_fall] = A1 * np.cos((np.pi / 2) * ((mod_t[p1_fall] - t1) / fall1))**2
    
    # Phase 2 - Rise (0 to spike2 over rise2)
    y[p2_rise] = A2 * np.sin((np.pi / 2) * ((mod_t[p2_rise] - t2) / rise2))**2
    
    # Phase 2 - Fall (spike2 to 0 over fall2)
    y[p2_fall] = A2 * np.cos((np.pi / 2) * ((mod_t[p2_fall] - t3) / fall2))**2

    if noise:
        rng = random.Random(noise_seed)
        for x in range(len(y)):
            y[x] += (rng.random() * noise * 2 - noise)

    # Generate metadata
    metadata = {
        "sample_rate_hz" : sample_rate,
        "duration_ms" : T,

        "baseline_uv": 0,

        "spike1_amplitude_uv" : A1,
        "spike2_amplitude_uv" : A2,

        "spike1_start_ms" : offset,
        "spike2_start_ms" : offset + rise1 + fall1,
        "spike2_end_ms" : offset + rise1 + fall1 + rise2 + fall2,

        "rise_time_ms" : rise1,
        "peak_to_trough_time_ms" : fall1 + rise1,
        "recovery_time_ms" : fall2,

        "noise_rms_v" : noise,
        "random_seed" : noise_seed,

        "waveform_type" : waveform_type,
        "test_case"     : test_case
    }

    export_waveform_csv(t, y, filename=test_case)
    
    return t, y, sample_rate, metadata

def export_waveform_csv(t, y, filename="waveform"):
    """
    Exports time and waveform arrays to a CSV file with headers 'time,amplitude'.
    """
    data = np.column_stack((t, y))
    np.savetxt(filename + '.csv', data, delimiter=",", header="time,amplitude", comments="", fmt="%.6f")
    #print(f"Saved {len(t)} samples to {filename}")

if __name__ == '__main__':
    # --- Parameters Configuration ---
    # --- Test Case 1 ---
    A1 = 80       # Positive amplitude
    A2 = -120       # Negative amplitude

    # Phase 1:
    rise1 = .300       
    fall1 = .250       

    # Phase 2:
    rise2 = .250       
    fall2 = 1.000       

    T = 5.0          # Total period in ms
    offset = 2.000      # Horizontal shift

    sample_rate = 1000000  # In Hz

    # Calculate the waveform amplitudes; t is now generated inside the function
    t_values, waveform, sr, metadata = generate_waveform(
        sample_rate, A1, A2, rise1, fall1, rise2, fall2, T, offset, 0, 1234, "biphasic", "positive_then_negative"
    )
    '''
    # --- Plotting with Matplotlib ---
    plt.figure(figsize=(10, 5))
    plt.plot(t_values, waveform, label='Fully Asymmetric Wave', color='forestgreen', linewidth=2)

    # Styling and labels
    plt.title('Biphasic Waveform with Independent Rise & Fall Times', fontsize=13, fontweight='bold')
    plt.xlabel('Time (t)', fontsize=12)
    plt.ylabel('Amplitude', fontsize=12)
    plt.axhline(0, color='black', linestyle='--', linewidth=0.8, alpha=0.7)  # Baseline reference
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.xlim(0, T)
    plt.ylim(-(max(abs(A1), abs(A2)) + 0.5), (max(abs(A1), abs(A2)) + 0.5))
    plt.legend(loc='upper right')

    # Display the plot
    plt.show()
    '''

    print(metadata)