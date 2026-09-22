# html/

The briefing page for the forest health plot network. One self contained static
site: open `index.html` in a browser, no build step and no server required.

It is the web twin of `Forest-Health-Monitoring-Plan.pptx` and covers the same
ground for people who would rather scroll than sit through slides. Arrow keys,
page keys, and space move between sections; the dots on the right jump; the
button top right forces light or dark.

## Files

```
html/
  index.html         content and structure, one <section class="slide"> per screen
  assets/eip.css     EIP brand tokens, layout, light and dark surfaces
  assets/app.js      Plotly charts, table views, navigation, theme toggle
  data/figures.js    every number the page shows   <- GENERATED, do not hand edit
```

## Updating the numbers

`data/figures.js` is written by `scripts/build_html_data.py`, which reads the
repo's own outputs rather than anything typed twice:

```
python scripts/build_html_data.py
```

Rerun it after `06_tessellation` regenerates the Basin grid, after the sample
size work changes, or after the threshold analysis is rerun. Text in
`index.html` pulls single values through `data-fig="path.to.value"` spans, so a
number quoted in a sentence updates with the chart beside it. Nothing in the
page is allowed to state a figure the repo cannot reproduce.

Every spatial source is a live TRPA REST service, listed under
`tessellation.sources` in `config.yaml`: the TRPA Boundary, Lake Tahoe, the CA
and NV state polygons, wilderness, urban area, ownership, EcObject seral stage,
and the aspen, meadow, and stream environment zone layers. Note the host is
maps.trpa.**org**, not .gov. Nothing here reads a downloaded snapshot, so the
page reflects whatever those services return on the day the builder ran, and the
generated date on the last section says when that was.

## Chart rules, and why they are what they are

The EIP palette has a trap in it. EIP green and EIP orange sit five units apart
in deuteranopic colour space, which is below the floor where a reader with the
commonest form of colour blindness can tell two adjacent categories apart. They
cannot carry data meaning against each other, whatever the brand deck shows
side by side.

So the charts use two colours: EIP blue for the series and EIP orange for the
one thing that earns emphasis, either a reference line or the option being
recommended. Dark mode uses lighter steps of the same two hues, chosen against
the navy surface rather than flipped automatically. Both pairs pass lightness,
chroma, colour vision separation, and contrast. Green stays in the interface on
labelled elements, where the label carries the meaning.

Beyond colour: every bar carries a direct value label, every figure has a
`Show the numbers` table underneath it, and no chart has two y axes.

## Publishing

The folder is self contained apart from two content delivery network
references, Google Fonts and Plotly. Copy `html/` to any static host, or push
it to the public `ForestHealth` repository and serve it from GitHub Pages. If
it has to work offline, vendor `plotly.min.js` into `assets/` and change the one
script tag.
