import argparse
import pandas as pd
import numpy as np
import yaml
import json
import logging
import time
import sys
import os


def setup_logger(log_file):
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


def write_metrics(output_path, metrics):
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--log-file", required=True)
    args = parser.parse_args()

    setup_logger(args.log_file)

    start_time = time.time()

    try:
        logging.info("Job started")

        # CONFIG LOAD
        if not os.path.exists(args.config):
            raise ValueError("Config file not found")

        with open(args.config, "r") as f:
            config = yaml.safe_load(f)

        for key in ["seed", "window", "version"]:
            if key not in config:
                raise ValueError(f"Missing config key: {key}")

        seed = config["seed"]
        window = config["window"]
        version = config["version"]

        np.random.seed(seed)
        logging.info(f"Config loaded: {config}")

        # DATA LOAD
        if not os.path.exists(args.input):
            raise ValueError("Input CSV not found")

        df = pd.read_csv(args.input)

        if df.empty:
            raise ValueError("CSV is empty")

        if "close" not in df.columns:
            raise ValueError("Missing 'close' column")

        logging.info(f"Rows loaded: {len(df)}")

        # ROLLING MEAN
        df["rolling_mean"] = df["close"].rolling(window).mean()

        # SIGNAL
        df["signal"] = (df["close"] > df["rolling_mean"]).astype(int)

        valid_df = df.dropna()

        signal_rate = valid_df["signal"].mean()

        latency = int((time.time() - start_time) * 1000)

        metrics = {
            "version": version,
            "rows_processed": len(df),
            "metric": "signal_rate",
            "value": round(float(signal_rate), 4),
            "latency_ms": latency,
            "seed": seed,
            "status": "success"
        }

        write_metrics(args.output, metrics)

        logging.info(f"Metrics: {metrics}")
        logging.info("Job completed")

        print(json.dumps(metrics, indent=2))
        sys.exit(0)

    except Exception as e:
        error_metrics = {
            "version": "v1",
            "status": "error",
            "error_message": str(e)
        }

        write_metrics(args.output, error_metrics)

        logging.error(str(e))
        print(json.dumps(error_metrics, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()