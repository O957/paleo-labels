# This Makefile is based somewhat on the Makefile present here:
# https://github.com/tompollard/phd_thesis_markdown/blob/main/Makefile

PANDOC=pandoc
BASEDIR=$(CURDIR)

pdf:
	pandoc  \
		--output "out.pdf" \
		--pdf-engine=xelatex \
		--pdf-engine-opt=--shell-escape \
		"$(BASEDIR)"/*.md


.PHONY: help install pdf docx html tex
