# This script fetches fauna entered into the
# Paleobiology Database.
#
# To run:
# Rscript fetch_pbdb_data.R (in ./assets/scripts)

library(paleobioDB)
library(jsonlite)
library(fs)
library(here)
library(dplyr)


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


final_save_path <- fs::path(save_dir, "pbdb_data_combined.json")


if (fs::file_exists(final_save_path)) {
  message(
    "Combined JSON already exists; skipping fetch: ",
    fs::path_file(final_save_path)
  )
  quit(status = 0)
}


time_intervals <- data.frame(
  min_ma = seq(0.5, 80, by = 10),
  max_ma = seq(10, 80, by = 10)
)


time_intervals$min_ma[1] <- 0.5

message("Fetching PBDB data in ", nrow(time_intervals), " batches...")


base_args <- list(
  limit = "all",
  show = c("full", "ages", "img", "strat", "crmod", "geo"),
  vocab = "pbdb"
)


all_dfs <- list()


for (i in 1:nrow(time_intervals)) {
  min_ma <- time_intervals$min_ma[i]
  max_ma <- time_intervals$max_ma[i]

  message(sprintf(
    "Fetching batch %d/%d: %g - %g Ma",
    i,
    nrow(time_intervals),
    min_ma,
    max_ma
  ))

  batch_file <- fs::path(
    save_dir,
    sprintf("pbdb_batch_%02d_%g_%g.json", i, min_ma, max_ma)
  )

  if (fs::file_exists(batch_file)) {
    message("Batch file exists, loading: ", fs::path_file(batch_file))
    batch_df <- jsonlite::fromJSON(batch_file, flatten = TRUE)
  } else {
    batch_args <- c(base_args, list(min_ma = min_ma, max_ma = max_ma))

    batch_df <- NULL
    max_retries <- 3
    retry_count <- 0

    while (is.null(batch_df) && retry_count < max_retries) {
      tryCatch(
        {
          batch_df <- do.call(paleobioDB::pbdb_occurrences, batch_args)
        },
        error = function(e) {
          retry_count <<- retry_count + 1
          message(
            "Error in batch ",
            i,
            ", retry ",
            retry_count,
            "/",
            max_retries,
            ": ",
            e$message
          )
          if (retry_count < max_retries) {
            Sys.sleep(10)
          }
        }
      )
    }

    if (is.null(batch_df)) {
      message(
        "Failed to fetch batch ",
        i,
        " after ",
        max_retries,
        " retries. Skipping."
      )
      next
    }

    write_pbdb_df_to_json(batch_df, batch_file)
  }

  if (!is.null(batch_df) && nrow(batch_df) > 0) {
    all_dfs[[i]] <- batch_df
    message("Batch ", i, " complete: ", nrow(batch_df), " records")
  } else {
    message("Batch ", i, " returned no data")
  }

  Sys.sleep(2)
}


if (length(all_dfs) > 0) {
  message("Combining ", length(all_dfs), " batches...")
  combined_df <- dplyr::bind_rows(all_dfs)

  if ("occurrence_no" %in% names(combined_df)) {
    combined_df <- combined_df[!duplicated(combined_df$occurrence_no), ]
  }

  message("Combined dataset: ", nrow(combined_df), " total records")

  write_pbdb_df_to_json(combined_df, final_save_path)
  message("PBDB data fetch completed successfully.")
} else {
  message("No data retrieved from any batch.")
}
