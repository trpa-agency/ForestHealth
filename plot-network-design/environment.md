# Environment

Default ArcGIS Pro Python environment:
`C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe`

geopandas, rasterio, shapely, numpy, pandas, scipy, and pyarrow are in arcgispro-py3. Install once:
```
conda install -n arcgispro-py3 -c conda-forge python-dotenv pyyaml scikit-image
```

scikit-image computes the hike distance for access classes (`skimage.graph.MCP_Geometric`). Without it the notebook falls back to planar distance and logs a warning.

R 4.x for the frozen selection: `install.packages(c("spsurvey", "sf"))`, spsurvey 5.x (tested with 5.7.0 on Oct 19, 2026). Set `run.rscript` to the Rscript path. The Python GRTS in `src/strata.py` is for iteration only.
