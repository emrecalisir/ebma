# EBMA rerun summary (tables only)

NDCG@K = N/A (not an item ranking task).

## layer2_novel

| dataset | method | Fid | FRS_k3 | portfolio_novelty | redundancy | coverage | code_path_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| online-retail-ii | A1_typed_beam | 1.0 | 0.90274739145069 | 0.8480110406748247 | 0.4174310662281927 | 0.08212722988892629 | a1_typed_beam_portfolio |
| online-retail-ii | A0_propose_verify | 1.0 | 0.9081538202625379 | 0.6942960168572861 | 0.32681519803943276 | 0.20582295523392796 | a0_schema_propose_verify |
| online-retail-ii | A2_freetext | 1.0 | 0.806441433860653 | 0.6406094842097656 | 0.3615359925416247 | 0.46516324469875464 | a2_nl_tag |
| online-retail-ii | A4_random | 1.0 | 0.7726144395826321 | 0.6911167314029134 | 0.108954710663511 | 1.0 | a4_uniform_catalogue |
| online-retail-ii | A5_rfm_fixed | 1.0 | 0.6588354089532145 | 0.0 | 0.1725057366343986 | 0.5955907101985863 | a5_rfm_fixed |
| online-retail-ii | RFM_quintile | 1.0 | 0.6463816896667789 | 0.0 | 0.1725057366343986 | 0.5955907101985863 | a5_rfm_fixed |
| online-retail-ii | propensity_logistic_RFM | 1.0 | 0.8683009835820337 | 0.5591063116977618 | 0.3966360854664744 | 0.20043756311006394 | propensity_logistic_rfm |
| online-retail-ii | BeamSD_WRAcc | 1.0 | 0.9235737125546954 | 0.6942960168572861 | 0.3268151980394327 | 0.20582295523392796 | beam_sd_wracc_no_portfolio |
| online-retail-ii | ExKMC_IMM_paths | 1.0 | 0.954750084146752 | 0.9329258558390181 | 0.049692016109926566 | 0.10148098283406261 | exkmc_kmeans_tree_path |
| online-retail-ii | Shi_persona_foil | 1.0 | 0.11334567485695052 | 0.004712218108380961 | 1.0 | 0.995287781891619 | shi_persona_foil |
| online-retail-ii | LACE_CtrlCE_foil | 1.0 | 0.8199469875462807 | 0.6642768010316983 | 0.3230625987709775 | 0.4594412655671491 | lace_nl_no_typed_freeze |
| complete-journey | A1_typed_beam | 1.0 | 0.611786148238153 | 0.9121963562753037 | 0.5427996597774861 | 0.02916160388821385 | a1_typed_beam_portfolio |
| complete-journey | A0_propose_verify | 1.0 | 0.59983799108951 | 0.895748987854251 | 0.4305555555555556 | 0.02916160388821385 | a0_schema_propose_verify |
| complete-journey | RFM_quintile | 1.0 | 0.5880113406237342 | 0.0 | 0.13148176151180668 | 0.6366950182260024 | a5_rfm_fixed |
| complete-journey | propensity_logistic_RFM | 1.0 | 0.6171189415417848 | 0.6979307242465137 | 0.28243970070289204 | 0.1644390441474281 | propensity_logistic_rfm |
| complete-journey | BeamSD_WRAcc | 1.0 | 0.6492507087889834 | 0.8671558704453441 | 0.9599728629579376 | 0.02713649250708789 | beam_sd_wracc_no_portfolio |
| complete-journey | ExKMC_IMM_paths | 1.0 | 0.871607938436614 | 0.8736798098926246 | 0.08609957061062122 | 0.35398946942081816 | exkmc_kmeans_tree_path |
| complete-journey | LACE_CtrlCE_foil | 1.0 | 0.5331105710814095 | 0.4376265694613204 | 0.41084769407984584 | 0.9384366140137708 | lace_nl_no_typed_freeze |
