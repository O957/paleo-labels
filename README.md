# Paleontological Labels

_`paleo-labels` is an application for writing precisely formatted labels singularly or in bulk for use with paleontological specimens, collections, and excursions._

This repository is in the earliest stages of development—there is not currently a minimum viable product yet—so please be patient and return in due course. Any suggestions or ideas would be appreciated, however, and can be provided as an issue in this repository (see [here](https://github.com/AFg6K7h4fhy2/paleo-labels/issues)) or email (see [here](https://github.com/AFg6K7h4fhy2#contact)).


## Utility Diagram

See [here](https://www.mermaidchart.com/play#pako:eNqrVkrOT0lVslJSqgUAFW4DVg) for the live Mermaid diagram editor.

```mermaid
%%{init: {"theme": "neutral", "themeVariables": { "fontFamily": "Iosevka", "fontSize": "25px", "lineColor": "#808b96", "arrowheadColor": "#808b96", "edgeStrokeWidth": "10px", "arrowheadLength": "20px"}}}%%
flowchart TD
    A["Label Maker"] --> Z1["File"]
    A["Label Maker"] --> Z2["Folder"]
    Z2["Folder"] -->|Full Preload| C["Label(s)"]
    Z1["File"] -->|Empty Preload| B1["Template"]
    Z1["File"] -->|Full Preload| C["Label"]
    Z1["File"] -->|Partial Preload| B2["Partial Label"]
    B2["Partial Label"] -->|Fill In Label| C["Label"]
    B1["Template"] -->|Fill In Label| C["Label(s)"]
    C["Label(s)"] -->|Style| D["Styled Label(s)"]
    C["Label(s)"] -->|Repeat?| Z1["File"]
    D["Styled Label(s)"] --> E1["PDF"]
    D["Styled Label(s)"] --> E2["Image(s)"]
    D["Styled Label(s)"] --> E3["TOML(s)"]
    D["Styled Label(s)"] --> E4["Json"]

    Y["Label Retriever"] --> X1["File"]
    Y["Label Retriever"] --> X2["Folder"]


    linkStyle default stroke: #808b96
    linkStyle default stroke-width: 2.0px
```


<details markdown=1>

<summary> A scene of strata of the latest Pliocene of Arizona, USA. </summary>

<img src="./assets/readme_photos/IMG_3764.jpg" width="550" />

</details>
