# This script fetches fauna entered into the Paleobiology
# Database.
#
# To run:
# Rscript ./assets/scripts/fetch_pbdb_data.R

library(paleobioDB)
library(jsonlite)
library(fs)
library(here)

save_dir <- here::here("data", "pbdb")
fs::dir_create(save_dir, recurse = TRUE)

write_pbdb_df_to_json <- function(pbdb_df, save_path) {
  if (!fs::file_exists(save_path)) {
    jsonlite::write_json(pbdb_df, save_path, pretty = TRUE, auto_unbox = TRUE)
    message("PBDB Data Written To Json: ", fs::path_file(save_path))
  } else {
    message(
      "(Skipping) PBDB Data Json File Already Exists: ",
      fs::path_file(save_path)
    )
  }
}


save_path <- fs::path(save_dir, "pbdb_data.json")

pbdb_args <- list(
  limit = "all",
  min_ma = 1000,
  max_ma = 0.5,
  show = c("full", "ages", "img", "strat", "crmod", "geo"),
  vocab = "pbdb"
)

if (fs::file_exists(save_path)) {
  message("JSON already exists; skipping fetch: ", fs::path_file(save_path))
} else {
  message("Fetching PBDB data...")
  df <- do.call(paleobioDB::pbdb_occurrences, pbdb_args)
  write_pbdb_df_to_json(df, save_path)
  message("PBDB data fetch completed.")
}
