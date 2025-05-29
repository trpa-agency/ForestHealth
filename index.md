# Forest Health Threshold Update

## Proposed Thresholds

This page outlines the proposed new threshold indicators for assessing forest health in the Lake Tahoe Basin. These indicators are intended to measure how current forest conditions compare to desired ecological standards. Grounded in the best available science and regional data, each indicator represents a key component of forest structure or ecological process that contributes to forest resilience and function. Together, they provide a framework for evaluating progress toward forest health goals.

---

## Stand Density

The table below presents the proposed threshold for **Stand Density**, reported in **Trees Per Acre (TPA)** and **Basal Area (BA in ft²/acre)**. These values help evaluate forest structure and crowding, which are critical for understanding forest health. Overstocked forests tend to have greater competition for water and nutrients, and higher risk of severe wildfire.

<iframe src="DataVisualizations/StandDensity_Table.html" width="100%" height="500" frameborder="0"></iframe>

#### Chart

The chart shows the distribution of tree density and basal area across the Basin. Values exceeding the proposed thresholds suggest areas where mechanical thinning, prescribed fire, or other treatments may be necessary to reduce fire risk and promote resilience.

<iframe src="DataVisualizations/StandDensity_Chart.html" width="100%" height="500" frameborder="0"></iframe>

---

## Composition

The seral stage metric describes the distribution of forest age classes. A resilient landscape contains a mix of early-, mid-, and late-seral forests, supporting biodiversity, regeneration, and adaptation to disturbance. Uniformly aging forests or dominance by a single stage can reduce ecological resilience and increase vulnerability to pests and catastrophic fire.

<iframe src="DataVisualizations/CompositionAge_Table.html" width="100%" height="500" frameborder="0"></iframe>

#### Chart

This chart compares the current forest composition (by age class) with desired reference conditions. It helps identify where recruitment of younger forests or retention of older stands may be lacking.

<iframe src="DataVisualizations/CompositionAge_Chart.html" width="100%" height="500" frameborder="0"></iframe>  

#### Map

This map displays the current forest composition.

<iframe src="DataVisualizations/CompositionAge_Map.html" width="100%" height="500" frameborder="0"></iframe>  

#### Questions about the map? 
   * Why is the Angora Fire not classified as Early Seral?

### Proposed Attainment Assessment

**Methods to Make a Threshold Attainment Call**

#### Define scoring for each class
Assign scores to how far each cell is from target range:

| Class                  | Score |
|------------------------|-------|
| Within Range           | 0     |
| Under/Over Represented | 1     |

#### Weight scores by acres
Give more weight to forest types that make up more of the basin.

> **Weighted score = Class score × Acres**

### Sum and normalize
Sum up the total possible weighted score (if all rows were "Under/Over") and compare to the actual weighted score.

#### Convert Ratio to Qualitative Call

To determine how close forest conditions are to targets:

1. **Assign a score** 
   - If the class is "Within Range", the score is 0.
   - If the class is "Under Represented" or "Over Represented", the score is 1.

2. **Weight the score by acres** 
   - Multiply the class score by the number of acres to get the weighted score.

3. **Calculate totals**:
   - Add up all weighted scores to get the total weighted score.
   - Also calculate the maximum possible score by assuming every class had a score of 1.

4. **Normalize**:
   - Compute the attainment ratio using the formula:  
     `attainment ratio = 1 - (total weighted score / maximum possible score)`

5. **Map the attainment ratio to a qualitative category**:

| Attainment Ratio | Category            |
|------------------|---------------------|
| > 0.85           | Considerably Better |
| 0.70 – 0.85      | Somewhat Better     |
| 0.50 – 0.70      | On Target           |
| 0.30 – 0.50      | Somewhat Worse      |
| < 0.30           | Considerably Worse  |

---

### Attainment Call: Somewhat Worse than Target

Analysis of forest structure across three major forest types shows a consistent underrepresentation of early and late open seral stages. Overrepresented mid-closed canopy stages dominate, especially in Jeffrey Pine and Mixed Conifer types. Weighted across the basin, only ~55% of seral structure is within desired conditions, resulting in a **“Somewhat Worse than Target”** call.

---

### Summary Table

| Forest Type               | % Within Range | Acres Evaluated | Notes                                |
|---------------------------|----------------|------------------|--------------------------------------|
| Jeffrey Pine              | 1/5 (20%)      | ~40,000          | Late open under; mid closed over     |
| Mixed Conifer / White Fir | 0/5 (0%)       | ~64,000          | Early and late both under            |
| Red Fir                   | 3/5 (60%)      | ~22,000          | Best performance, still mid over     |
| **Total**                 | ~27%           | ~126,000         | Red fir closer to target than others |

---

## Wildland Urban Interface (WUI) Wildfire Protection

The Wildland Urban Interface (WUI) is where homes and communities meet wild, undeveloped lands. In the Lake Tahoe region, nearly half the area falls within the WUI, divided into the **Defense Zone** — the immediate buffer around structures and evacuation routes — and the **Threat Zone**, which surrounds the Defense Zone and focuses on reducing fire starts.

Effective wildfire protection aims to reduce flame lengths during extreme fire weather to **4 feet or less** within the Defense Zone, allowing firefighters to suppress fires before they threaten structures.

#### Proposed Standard

- Predicted flame lengths under 90th percentile fire weather conditions shall be **less than 4 feet across 90% of the WUI Defense Zone**.
- Evaluation should ensure that areas exceeding 4-foot flame lengths are:
  - Well distributed,
  - Patch size under 1 acre,
  - Not within 100 feet of structures or critical infrastructure.

#### Current Condition

Wildfire risk was modeled using the **FSim Wildfire Risk Simulation Software**, which integrates current fuels, topography, historic weather, and fire occurrence to predict fire likelihood and intensity. These data help assess wildfire vulnerability and guide targeted fuel reduction in priority areas.

---

## Functional Fire

This indicator assesses **fire severity** . The goal is to evaluate whether wildfire activity has been ecologically beneficial or harmful. Functional fire maintains ecosystem processes and structure, whereas uncharacteristically high-severity fire can degrade habitat and soil productivity.

**By Management Zone:**

#### Chart

This chart shows the proportion of burned area by severity category (low, moderate, high) within each zone. These summaries support region-specific assessments of fire impacts and recovery needs.

<iframe src="DataVisualizations/FireSeverityByManagementZone_Chart.html" width="100%" height="500" frameborder="0"></iframe>  

#### Map

The map visualizes fire severity spatially, allowing planners to assess patterns and identify areas where ecological fire may have been lost or maintained.

<iframe src="DataVisualizations/FireSeverityByManagementZone_Map.html" width="100%" height="750" frameborder="0"></iframe>  

---

## Performance Measures

In addition to ecological thresholds, performance measures track **management activities** like fuel reduction. These metrics help determine whether restoration efforts are keeping pace with ecological needs and regional goals.

---

### Forest Fuels Treatments

#### Chart

The chart summarizes annual forest fuels treatment activity over time, including thinning, mastication, and prescribed burning. Understanding these trends informs whether management is occurring at sufficient pace and scale.

<iframe src="DataVisualizations/FuelTreatment_Chart.html" width="100%" height="500" frameborder="0"></iframe>  

#### Map

The map shows the spatial extent of past fuel treatments, which can be compared with fire severity and stand density data to assess treatment effectiveness.

<iframe src="DataVisualizations/FuelTreatment_Map.html" width="100%" height="750" frameborder="0"></iframe>  

---

## Data Sources

The forest health metrics presented here rely heavily on spatial datasets compiled and maintained by the California Wildfire Taskforce's Regional Resource Kit project. These datasets include high-resolution vegetation composition, forest type, stand structure, and fire severity layers developed through advanced remote sensing and ecological modeling. The Regional Resource Kits provide a comprehensive foundation for assessing forest conditions across the Lake Tahoe Basin and support local restoration and fire resilience planning.

Learn more and access the original data sources here:  
[Regional Resource Kits - Wildfire Task Force](https://wildfiretaskforce.org/regional-resource-kits-page/)

---

## 📓 Methods & Results

All metrics were derived from high-resolution remote sensing datasets. The methodology emphasizes transparency, repeatability, and alignment with regional forest goals. Thresholds were developed based on literature review and expert input.

- 📘 **Analysis Notebook:**  
  [ForestHealth_ThresholdUpdate_Analysis.ipynb](https://github.com/trpa-agency/ForestHealth/blob/main/ForestHealth_ThreholdUpdate_Anlaysis.ipynb)  
  Contains the logic, thresholds, and data processing steps used to generate stand density, seral stage, and fire severity metrics.

- 📗 **Results Notebook:**  
  [ForestHealth_ThresholdUpdate_Results.ipynb](https://github.com/trpa-agency/ForestHealth/blob/main/ForestHealth_ThresholdUpdate_Results.ipynb)  
  Creates the summary charts, maps, and tables featured in this results page.
