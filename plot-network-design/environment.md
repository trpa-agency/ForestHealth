# Environment

Default ArcGIS Pro Python environment:
`C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe`

geopandas, rasterio, shapely, numpy, pandas, scipy, and pyarrow are in arcgispro-py3. Install once:
```
conda install -n arcgispro-py3 -c conda-forge python-dotenv pyyaml
```

R 4.x for the frozen draw: `install.packages(c("spsurvey", "sf"))`. The Python GRTS in `src/strata.py` is for iteration; the frozen design is drawn with spsurvey for parity with TEON's backbone.
