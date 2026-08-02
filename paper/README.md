# Research paper

`subtraction-study.tex` is a self-contained paper source for the completed
larger-refactor replication. The rendered paper is committed as
`subtraction-study.pdf`.

## Build

From the repository root, using the lightweight Tectonic distribution:

```sh
tectonic --outdir paper paper/subtraction-study.tex
```

The conventional TeX toolchain also works from the `paper/` directory:

```sh
cd paper
latexmk -pdf subtraction-study.tex
```

If `latexmk` is unavailable:

```sh
cd paper
pdflatex subtraction-study.tex
pdflatex subtraction-study.tex
```

The committed Markdown findings and JSON evidence remain the canonical
machine-readable record. The PDF is a reader-friendly rendering of the same
bounded result.
