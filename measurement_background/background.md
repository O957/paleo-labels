---
title: "Fossil Measurement Sheet"
author: "AF & Friends"
date: "The 21st Century"
output: pdf_document
papersize: letter
mainfont: TeX Gyre Schola
fontsize: 12pt
header-includes:
- \usepackage{tikz}
- \usepackage{geometry}
- \geometry{margin=1in}
- \usepackage{fancyhdr}
- \pagestyle{fancy}
- \fancyfoot[C]{\thepage}
- \fancyhead{}
- \fancyhead[L]{\textit{Fossil Measurement}}
- \fancyhead[R]{\textsc{AF And Friends}}
---



\begin{center}
\begin{tikzpicture}
  % define grid dimensions
  \draw[step=1mm, gray, very thin] (0,0) grid (15,15); % Smaller grid with 1mm x 1mm divisions
  \draw[step=1cm, black, thick] (0,0) grid (15,15);  % Larger grid with 1cm x 1cm divisions
\end{tikzpicture}
\end{center}

\newpage

\begin{center}
\begin{tikzpicture}
  % define grid dimensions
  \draw[step=1mm, gray, very thin] (0,0) grid (15,20); % Smaller grid with 1mm x 1mm divisions
  \draw[step=1cm, black, thick] (0,0) grid (15,20);  % Larger grid with 1cm x 1cm divisions
\end{tikzpicture}
\end{center}

\newpage

\begin{center}
\begin{tikzpicture}
  % draw the grid using inches
  \draw[step=0.25in, gray, very thin] (0,0) grid (6in,8in); % Smaller grid with 0.25 inch (1/10 inch) divisions
  \draw[step=1in, black, thick] (0,0) grid (6in,8in);  % Larger grid with 1 inch divisions
\end{tikzpicture}
\end{center}

\newpage

\begin{center}
\begin{tikzpicture}
  % draw the grid using inches
  \draw[step=0.25in, gray, very thin] (0,0) grid (6in,8in); % Smaller grid with 0.25 inch (1/10 inch) divisions
  \draw[step=1in, black, thick] (0,0) grid (6in,8in);  % Larger grid with 1 inch divisions
\end{tikzpicture}
\end{center}

<!--
FIRST ATTEMPT

\begin{tikzpicture}
  \draw[step=1mm, gray, very thin] (0,0) grid (19,25); % Smaller grid with 1mm x 1mm divisions
  \draw[step=1cm, black, thick] (0,0) grid (19,25);  % Larger grid with 1cm x 1cm divisions
\end{tikzpicture} -->
