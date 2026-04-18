# Findings · Main Results

## Result Highlights

- `Voltage-aware tapered proxy search beyond the 4.15C incumbent`: VTBO pushed the frontier beyond the 4.15C incumbent and improved nominal Q30 by +5.62% over BO_3step_aggressive while keeping full guard feasibility. (Q30=0.09494; plating_loss=0.32184; sei_growth=57.54798; total_lli=0.01402536)
- `UA_EVTBO v1 bounded robust search on followup_v1`: EVTBO improved nominal Q30 over VTBO while preserving success_rate=1.0 and guard_pass_rate=1.0, becoming the last previous SOTA line before PSMS-v2. (Q30=0.09522; plating_loss=0.32184; sei_growth=57.53493; total_lli=0.01402490)
- `PSMS-v2 larger-budget robust search beyond the EVTBO anchor`: PSMS-v2 promoted UA5_PSMS_3.00C_rest10m_4.30C_e4.50_v4p18_h3.35_1p5m as the robust top protocol. Nominal Q30 improved by +7.19% over BO_3step_aggressive and by +1.20% over EVTBO, while plating_loss stayed flat and both sei_growth and total_lli improved. (Q30=0.09636; plating_loss=0.32184; sei_growth=57.48976; total_lli=0.01402332)
