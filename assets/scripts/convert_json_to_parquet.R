# This script converts a fetched `json` data file from
# the Paleobiology Database into a parquet file.
#
# To run:
# Rscript ./assets/scripts/convert_json_to_parquet.R

library(jsonlite)
library(arrow)
library(fs)
library(here)

data_dir <- here::here("data", "pbdb")
if (!fs::dir_exists(data_dir)) {
  stop("Data directory does not exist: ", data_dir)
}

json_files <- fs::dir_ls(data_dir, glob = "*.json")

if (length(json_files) == 0) {
  message("No JSON files found in: ", data_dir)
  quit(status = 0)
}

for (json_file in json_files) {
  parquet_file <- fs::path_ext_set(json_file, "parquet")

  if (fs::file_exists(parquet_file)) {
    message(
      "Parquet exists; skip conversion: ",
      fs::path_file(parquet_file)
    )
    next
  }

  message("Converting to parquet: ", fs::path_file(json_file))
  df <- jsonlite::fromJSON(json_file, flatten = TRUE)
  arrow::write_parquet(df, parquet_file)
  message("Wrote parquet: ", fs::path_file(parquet_file))
}

message("JSON to Parquet conversion completed.")
