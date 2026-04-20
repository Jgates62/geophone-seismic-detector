import pandas as pd
import numpy as np
import os

class SeismicFeatureEngineer:
    def __init__(self, dataframe, signal_column='Filtered'):
        """
        Initializes the feature engineer with a pandas DataFrame.
        :param dataframe: Raw pandas DataFrame loaded from the logger CSV.
        :param signal_column: The target column to generate features from.
        """
        self.df = dataframe.copy()
        self.signal_col = signal_column
        
        # Ensure the signal column is numeric, forcing errors to NaN
        self.df[self.signal_col] = pd.to_numeric(self.df[self.signal_col], errors='coerce')
        
        # Forward-fill any NaN values that might have occurred during serial boot
        self.df[self.signal_col] = self.df[self.signal_col].ffill().fillna(0)

    def add_rolling_variance(self, window=50):
        """Calculates the variance over a rolling window. Great for finding transient impacts."""
        col_name = f'Variance_w{window}'
        self.df[col_name] = self.df[self.signal_col].rolling(window=window).var()
        return self

    def add_signal_energy(self, window=50):
        """Calculates the sum of squared amplitudes. High energy = heavy footstep."""
        col_name = f'Energy_w{window}'
        sq_signal = self.df[self.signal_col] ** 2
        self.df[col_name] = sq_signal.rolling(window=window).sum()
        return self

    def add_sta_lta(self, sta_window=40, lta_window=800):
        """
        Short-Term Average / Long-Term Average.
        The premier algorithm for seismic event triggering.
        """
        col_name = f'STA_LTA_{sta_window}_{lta_window}'
        sq_signal = self.df[self.signal_col] ** 2
        
        sta = sq_signal.rolling(window=sta_window).mean()
        lta = sq_signal.rolling(window=lta_window).mean()
        
        # Add a tiny epsilon (1e-10) to LTA to prevent division by zero
        self.df[col_name] = sta / (lta + 1e-10)
        return self

    def add_zero_crossing_rate(self, window=50):
        """
        Calculates how often the signal crosses zero. 
        Serves as a lightweight proxy for frequency content.
        """
        col_name = f'ZCR_w{window}'
        
        # Create a boolean series where True means the sign changed from the previous row
        sign_changes = np.sign(self.df[self.signal_col]).diff().ne(0) & (self.df[self.signal_col] != 0)
        
        # Count the number of changes in the rolling window
        self.df[col_name] = sign_changes.rolling(window=window).sum()
        return self

    def add_rolling_max(self, window=50):
        """Captures the peak amplitude in a given window."""
        col_name = f'Max_w{window}'
        self.df[col_name] = self.df[self.signal_col].rolling(window=window).max()
        return self

    def get_dataframe(self):
        """Returns the fully engineered dataframe, dropping the initial NaN rows caused by rolling windows."""
        return self.df.dropna().reset_index(drop=True)


# ==========================================
# Example Usage
# ==========================================
if __name__ == "__main__":
    # Replace with your actual CSV filename
    input_file = "seismic_data_2026-04-20_08-13-49.csv" 
    
    if os.path.exists(input_file):
        print(f"Loading {input_file}...")
        raw_df = pd.read_csv(input_file)
        
        # Initialize the engineer class targeting the 'Filtered' column
        engineer = SeismicFeatureEngineer(raw_df, signal_column='Filtered')
        
        # Chain the methods to build your feature set
        # Note: Assuming ~860 Samples Per Second (SPS):
        # 40 samples ~ 0.05 seconds (Short thump)
        # 800 samples ~ 1 second (Background noise)
        processed_df = (engineer
                        .add_rolling_variance(window=40)
                        .add_signal_energy(window=40)
                        .add_zero_crossing_rate(window=40)
                        .add_sta_lta(sta_window=40, lta_window=800)
                        .get_dataframe())
        
        # Save the new dataset ready for ML training
        output_file = input_file.replace(".csv", "_features.csv")
        processed_df.to_csv(output_file, index=False)
        
        print(f"Feature engineering complete. Saved to {output_file}")
        print("\nData Preview:")
        print(processed_df.head())
    else:
        print(f"File {input_file} not found. Please provide a valid CSV.")