# Rerun diff, 2026-09-23

Type 2 was labeled White Fir before this run and Sierran Mixed Conifer after; rows are matched on that.

## Stand density

```
          Forest Type Seral Stage  Total Acres old  Total Acres new  Acres Meeting Threshold old  Acres Meeting Threshold new  Percent Meeting Threshold old  Percent Meeting Threshold new
         Jeffrey Pine       Early           796.62           696.10                       788.83                       696.10                          99.02                         100.00
         Jeffrey Pine        Late         11227.14          7103.74                       596.68                       491.27                           5.31                           6.92
         Jeffrey Pine         Mid         16759.65         12855.53                       654.06                       510.40                           3.90                           3.97
              Red Fir       Early           491.05           491.05                       484.60                       484.60                          98.69                          98.69
              Red Fir        Late         10913.34         10913.36                      7359.70                      7359.71                          67.44                          67.44
              Red Fir         Mid         10960.49         10960.51                      4746.34                      4746.35                          43.30                          43.30
Sierran Mixed Conifer       Early          2205.93          2306.46                      2205.49                      2304.46                          99.98                          99.91
Sierran Mixed Conifer        Late         22223.22         26346.67                      8541.28                     10255.07                          38.43                          38.92
Sierran Mixed Conifer         Mid         35846.88         39751.08                      6426.53                      7613.02                          17.93                          19.15
```

- basin old: 31,804 of 111,424 acres meeting, 28.5 percent
- basin new: 34,461 of 111,424 acres meeting, 30.9 percent

## Seral stage and canopy cover

Old mid and late labels were transposed (an old 'closed' row holds open pixels), so a label-matched row is not the same population. Compare the class shares, not the rows.

```
          Forest Type          Seral Stage Desired % Range Classification old  Current Area % old  Area (acres) old  Acres from Target old Classification new  Current Area % new  Area (acres) new  Acres from Target new
         Jeffrey Pine                Early           5–15%   Underrepresented                2.77            796.62                 642.55   Underrepresented                3.37            696.10                 336.67
         Jeffrey Pine Late (closed canopy)           5–10%    Overrepresented               13.12           3776.49                -898.14    Overrepresented               23.05           4760.14               -2694.60
         Jeffrey Pine   Late (open canopy)          40–50%   Underrepresented               25.89           7450.67                4062.71   Underrepresented               11.35           2343.60                5918.55
         Jeffrey Pine  Mid (closed canopy)           5–10%    Overrepresented               30.53           8787.49               -5909.14    Overrepresented               30.12           6221.50               -4155.96
         Jeffrey Pine    Mid (open canopy)          25–30%             Within               27.70           7972.19                   0.00    Overrepresented               32.12           6634.04                -437.43
              Red Fir                Early          10–20%   Underrepresented                2.20            491.05                1745.44   Underrepresented                2.20            491.05                1745.44
              Red Fir Late (closed canopy)          20–30%             Within               29.45           6587.34                   0.00   Underrepresented               19.34           4326.02                 146.96
              Red Fir   Late (open canopy)          30–40%   Underrepresented               19.34           4326.02                2383.45   Underrepresented               29.45           6587.34                 122.14
              Red Fir  Mid (closed canopy)          15–25%    Overrepresented               36.52           8168.34               -2577.11   Underrepresented               12.48           2792.17                 562.57
              Red Fir    Mid (open canopy)          15–25%   Underrepresented               12.48           2792.17                 562.57    Overrepresented               36.52           8168.34               -2577.11
Sierran Mixed Conifer                Early          10–20%   Underrepresented                3.66           2205.93                3821.68   Underrepresented                3.37           2306.46                4533.96
Sierran Mixed Conifer Late (closed canopy)          15–25%             Within               17.24          10389.84                   0.00             Within               19.84          13574.31                   0.00
Sierran Mixed Conifer   Late (open canopy)          25–35%   Underrepresented               19.63          11833.41                3235.62   Underrepresented               18.67          12772.36                4328.69
Sierran Mixed Conifer  Mid (closed canopy)           5–15%    Overrepresented               37.09          22354.46              -13313.04    Overrepresented               21.09          14424.53               -4163.90
Sierran Mixed Conifer    Mid (open canopy)          15–20%    Overrepresented               22.38          13492.47               -1437.25    Overrepresented               37.02          25326.55              -11645.71
```

### Basin-wide

```
                    metric     acres  percent_of_frame
               share_Early   3493.61              3.14
 share_Mid (closed canopy)  23438.20             21.04
   share_Mid (open canopy)  40128.93             36.01
  share_Late (open canopy)  21703.30             19.48
share_Late (closed canopy)  22660.47             20.34
            assessed_acres 111424.51            100.00
        within_class_acres  13574.31             12.18
       not_in_excess_acres  85749.80             76.96
       report_within_acres  70836.00             63.57
```
