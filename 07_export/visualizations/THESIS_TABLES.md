# Thesis tables

These CSV files are intended for native LaTeX tables, not screenshots.
The Markdown below is a compact preview; the CSV files contain the complete results.

## 01_dataset_statistics

| Dataset | Entities | Relations | Structural triples | Text literal rows |
| --- | --- | --- | --- | --- |
| YAGO | 99313458 | 68 | 176573872 | 1460695796 |
| SemOpenAlex | 1936550634 | 31 | 9617571538 | 499277625 |

## 02_link_prediction

| Dataset | Model | Loss | Positive rank | MRR | Hits@1 | Hits@10 | Hits@50 | AUC | Test triples |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| YAGO | TransE | 6.03402 | 12.8262 | 0.436647 | 0.334888 | 0.617155 | 0.985629 | 0.767641 | 176574 |
| YAGO | DistMult | 45.9918 | 14.0518 | 0.497625 | 0.418131 | 0.619947 | 0.970344 | 0.743793 | 176574 |
| YAGO | ComplEx | 52.2753 | 14.8 | 0.479053 | 0.400654 | 0.600819 | 0.961512 | 0.729309 | 176574 |
| SemOpenAlex | TransE | 1.8142 | 4.49008 | 0.78692 | 0.72418 | 0.90016 | 0.99626 | 0.93148 | 50000 |
| SemOpenAlex | DistMult | 9.83882 | 3.73286 | 0.837252 | 0.79984 | 0.90671 | 0.99953 | 0.94758 | 50000 |
| SemOpenAlex | ComplEx | 10.7943 | 3.80447 | 0.83612 | 0.79939 | 0.90405 | 0.99968 | 0.94556 | 50000 |

## 03_candidate_attrition

| Stage | Count |
| --- | --- |
| Raw exact-label pairs | 328835064 |
| After label/frequency filters | 29446511 |
| Ambiguous pair rows | 28060904 |
| Embedding top-1 | 2541303 |
| Embedding score ≥ 0.30 | 1980930 |
| Type-compatible at 0.30 | 1386057 |
| Final Stage 05 one-to-one | 1755590 |

## 04_threshold_sweep

| threshold | total_top1 | score_pass | type_pass | type_fail | score_pass_pct | type_pass_pct_of_total | type_fail_pct_of_score_pass | score_min | score_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.2 | 2541303 | 2387571 | 1689527 | 698044 | 0.939507 | 0.664827 | 0.292366 | -0.24573536 | 0.78252709 |
| 0.25 | 2541303 | 2236068 | 1580400 | 655668 | 0.87989 | 0.621886 | 0.293224 | -0.24573536 | 0.78252709 |
| 0.3 | 2541303 | 1980930 | 1386057 | 594873 | 0.779494 | 0.545412 | 0.3003 | -0.24573536 | 0.78252709 |
| 0.35 | 2541303 | 1567924 | 1069348 | 498576 | 0.616976 | 0.420787 | 0.317985 | -0.24573536 | 0.78252709 |
| 0.4 | 2541303 | 991727 | 668696 | 323031 | 0.390244 | 0.263131 | 0.325726 | -0.24573536 | 0.78252709 |
| 0.45 | 2541303 | 445523 | 313609 | 131914 | 0.175313 | 0.123405 | 0.296088 | -0.24573536 | 0.78252709 |
| 0.5 | 2541303 | 134850 | 101620 | 33230 | 0.053063 | 0.039987 | 0.246422 | -0.24573536 | 0.78252709 |
| 0.55 | 2541303 | 25541 | 20071 | 5470 | 0.01005 | 0.007898 | 0.214165 | -0.24573536 | 0.78252709 |
| 0.6 | 2541303 | 2821 | 2297 | 524 | 0.00111 | 0.000904 | 0.18575 | -0.24573536 | 0.78252709 |

## 05_system_comparison

| system | rows | pairs_in_proxy_gold | proxy_precision_like | proxy_recall_like | shared_with_baseline | baseline_only | system_only | author_count | work_count | institution_count | source_count | low_embedding_count | System |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 1755590 | 947748 | 0.539846 | 0.683995 | 1755590 | 0 | 0 | 1546286 | 172389 | 26490 | 7291 | 0 | Baseline |
| A+B | 1977402 | 951866 | 0.481372 | 0.686967 | 1630402 | 125188 | 347000 | 1657177 | 276881 | 27361 | 11392 | 194926 | A+B |
| C only | 1931659 | 951866 | 0.492771 | 0.686967 | 1694474 | 61116 | 237185 | 1643027 | 245451 | 27045 | 11815 | 131652 | C only |
| A+B+C final | 1973194 | 951866 | 0.482399 | 0.686967 | 1629924 | 125666 | 343270 | 1656666 | 273299 | 27355 | 11373 | 191785 | A+B+C |

## 06_sensitivity

| variant | embedding_weight | profile_weight | neighbor_weight | threshold | final_alignments | final_pairs_in_proxy_gold | proxy_precision_like | proxy_recall_like | shared_pairs | baseline_only_pairs | enriched_only_pairs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| abc_w060_035_005_t025 | 0.6 | 0.35 | 0.05 | 0.25 | 1976656 | 951866 | 0.481554 | 0.686967 | 1630309 | 125281 | 346347 |
| abc_w055_035_010_t025 | 0.55 | 0.35 | 0.1 | 0.25 | 1975809 | 951866 | 0.48176 | 0.686967 | 1630200 | 125390 | 345609 |
| abc_w065_030_005_t025 | 0.65 | 0.3 | 0.05 | 0.25 | 1976685 | 951866 | 0.481547 | 0.686967 | 1630389 | 125201 | 346296 |
| abc_w060_035_005_t030 | 0.6 | 0.35 | 0.05 | 0.3 | 1973194 | 951866 | 0.482399 | 0.686967 | 1629924 | 125666 | 343270 |
| abc_w060_035_005_t020 | 0.6 | 0.35 | 0.05 | 0.2 | 1977402 | 951866 | 0.481372 | 0.686967 | 1630402 | 125188 | 347000 |

## 07_evidence_descriptives

| Group | embedding_cosine_count | embedding_cosine_mean | embedding_cosine_std | embedding_cosine_median | embedding_cosine_min | embedding_cosine_max | profile_tfidf_score_count | profile_tfidf_score_mean | profile_tfidf_score_std | profile_tfidf_score_median | profile_tfidf_score_min | profile_tfidf_score_max | neighbor_tfidf_score_count | neighbor_tfidf_score_mean | neighbor_tfidf_score_std | neighbor_tfidf_score_median | neighbor_tfidf_score_min | neighbor_tfidf_score_max | abc_score_count | abc_score_mean | abc_score_std | abc_score_median | abc_score_min | abc_score_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline-shared | 12000 | 0.4098701992141666 | 0.0640581941186956 | 0.40510711 | 0.30001578 | 0.7490657 | 12000 | 0.9825956939908334 | 0.0516159936933758 | 1.0 | 0.19732871 | 1.0 | 12000 | 0.0187280920774999 | 0.0170251020148586 | 0.01755877 | 0.00345545 | 0.6374918 | 12000 | 0.5907670170291667 | 0.0431870320460586 | 0.5897352595 | 0.3140278165 | 0.8007068544999999 |
| Final-only | 12000 | 0.2992519446616666 | 0.0703083538066383 | 0.28301902 | 0.20000526 | 0.64894164 | 12000 | 0.9617746221916668 | 0.0873108591611281 | 0.995448065 | 0.18283723 | 1.0 | 12000 | 0.0244993830683333 | 0.0512582526103687 | 0.01865421 | 0.00372321 | 0.66633434 | 12000 | 0.5173972537175 | 0.0535822715957189 | 0.5139279379999999 | 0.300053649 | 0.7396354334999999 |
| Proxy-gold | 12000 | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 | 12000 | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 | 12000 | 0.0230137495866666 | 0.0372696873231895 | 0.01865421 | 0.0045489 | 0.6374918 | 12000 | 0.9511506874793332 | 0.0018634843661594 | 0.9509327105 | 0.950227445 | 0.98187459 |
| Threshold-rejected | 3462 | 0.2757929517042172 | 0.055055629546604 | 0.26582952 | 0.20002684 | 0.49657941 | 3462 | 0.3095523982380127 | 0.0989516100852421 | 0.32222874 | 0.0 | 0.50518616 | 3462 | 0.0221491374119006 | 0.0095451691577223 | 0.02174165 | 0.00287429 | 0.32435089 | 3462 | 0.2749265672764298 | 0.0143352936770559 | 0.2748391672499999 | 0.2500000264999999 | 0.2999898179999999 |

## 08_final_type_distribution

| semopenalex_type | count |
| --- | --- |
| author | 1656666 |
| work | 273299 |
| institution | 27355 |
| source | 11373 |
| publisher | 1553 |
| concept | 1526 |
| funder | 1074 |
| keyword | 343 |
| subfield | 3 |
| topic | 1 |
| field | 1 |

## 09_relation_distribution

| Dataset | relation | relation_uri | relation_id | count | share | cumulative |
| --- | --- | --- | --- | --- | --- | --- |
| YAGO | type | http://www.w3.org/1999/02/22-rdf-syntax-ns#type | 23 | 52604 | 0.2979147552867353 | 0.2979147552867353 |
| YAGO | sameAs | http://www.w3.org/2002/07/owl#sameAs | 13 | 49557 | 0.280658534099018 | 0.5785732893857534 |
| YAGO | location | http://schema.org/location | 5 | 22517 | 0.1275216056724093 | 0.7060948950581627 |
| YAGO | gender | http://schema.org/gender | 19 | 8697 | 0.0492541370756736 | 0.7553490321338363 |
| YAGO | author | http://schema.org/author | 11 | 4020 | 0.0227666587379795 | 0.7781156908718159 |
| YAGO | parentTaxon | http://schema.org/parentTaxon | 28 | 3660 | 0.0207278534778619 | 0.7988435443496779 |
| YAGO | inLanguage | http://schema.org/inLanguage | 37 | 3436 | 0.0194592635382332 | 0.8183028078879111 |
| YAGO | nationality | http://schema.org/nationality | 20 | 3258 | 0.018451187604064 | 0.8367539954919752 |
| YAGO | birthPlace | http://schema.org/birthPlace | 22 | 3201 | 0.018128376771212 | 0.8548823722631872 |
| YAGO | about | http://schema.org/about | 46 | 2950 | 0.0167068764370745 | 0.8715892487002618 |
| YAGO | knowsLanguage | http://schema.org/knowsLanguage | 21 | 2541 | 0.0143905671276631 | 0.885979815827925 |
| YAGO | alumniOf | http://schema.org/alumniOf | 10 | 2457 | 0.0139148459003024 | 0.8998946617282274 |
| YAGO | memberOf | http://schema.org/memberOf | 0 | 2453 | 0.0138921925085233 | 0.9137868542367508 |
| YAGO | children | http://schema.org/children | 3 | 1628 | 0.0092199304540872 | 0.923006784690838 |
| YAGO | worksFor | http://schema.org/worksFor | 1 | 1573 | 0.0089084463171248 | 0.9319152310079628 |
| YAGO | material | http://schema.org/material | 55 | 1390 | 0.0078720536432317 | 0.9397872846511944 |
| YAGO | actor | http://schema.org/actor | 16 | 1332 | 0.007543579462435 | 0.9473308641136295 |
| YAGO | award | http://schema.org/award | 8 | 1293 | 0.0073227088925889 | 0.9546535730062184 |
| YAGO | deathPlace | http://schema.org/deathPlace | 29 | 1280 | 0.0072490853693069 | 0.9619026583755254 |
| YAGO | neighbors | http://yago-knowledge.org/resource/neighbors | 7 | 836 | 0.0047345588818285 | 0.966637217257354 |

## 10_semantic_rejections

| YAGO profile | SemOpenAlex type | Rejected |
| --- | --- | --- |
| creative_work_like | author | 26339 |
| place_like | author | 19435 |
| person_like | work | 13871 |
| organization_like | author | 12360 |
| place_like | work | 8954 |
| organization_like | work | 8421 |
| event_like | work | 3358 |
| organism_like | work | 2365 |
| product_like | work | 2328 |
| other_typed | work | 2136 |
| other_typed | author | 600 |
| event_like | author | 490 |
| other_typed | concept | 279 |
| product_like | author | 240 |
| intangible_like | work | 225 |
| creative_work_like | institution | 215 |
| event_like | concept | 183 |
| intangible_like | author | 147 |
| product_like | concept | 113 |
| event_like | source | 104 |

## 11_sample_graph_statistics

| Graph | Nodes | Edges | Average degree | Median degree | Max degree | Density | Components |
| --- | --- | --- | --- | --- | --- | --- | --- |
| YAGO held-out | 263202 | 176574 | 1.341737524790845 | 1.0 | 6474 | 5.097767579875628e-06 | 86628 |
| SemOpenAlex 100k sample | 175031 | 100000 | 1.14265472973359 | 1.0 | 2763 | 6.528336455085357e-06 | 75061 |

## 12_type_profiles

| Dataset | Class | rdf:type triples |
| --- | --- | --- |
| YAGO | Librarian | 19 |
| YAGO | Catholic_priest | 73 |
| YAGO | Freguesia | 7 |
| YAGO | Class | 109 |
| YAGO | Politician | 732 |
| YAGO | Aircraft_pilot | 10 |
| YAGO | Film_actor | 61 |
| YAGO | Cave_With_Prehistoric_Art_Q11269813 | 2 |
| YAGO | Screenwriter | 60 |
| YAGO | Corporation | 170 |
| YAGO | Taxon | 3434 |
| YAGO | Television_film | 21 |
| YAGO | Ortsteil_Q253019 | 49 |
| YAGO | Geologist | 6 |
| YAGO | Uefa_Euro_2008_Team_Q115647743 | 1 |
| YAGO | Brewery | 1 |
| YAGO | University_Teacher_Q1622272 | 221 |
| YAGO | Literary_Work_Q7725634 | 167 |
| YAGO | Historian | 94 |
| YAGO | Film_director | 78 |

## 13_proxy_gold_by_type

| Type | Proxy total | Recovered | Proxy recall-like |
| --- | --- | --- | --- |
| author | 1044728 | 766187 | 0.7333841918662083 |
| work | 291624 | 151367 | 0.5190485008092612 |
| concept | 11411 | 377 | 0.0330382963806853 |
| source | 6076 | 5209 | 0.8573074391046741 |
| institution | 28098 | 26524 | 0.9439817780624956 |
| publisher | 1399 | 1294 | 0.9249463902787706 |
| funder | 2218 | 890 | 0.4012623985572588 |
| keyword | 51 | 16 | 0.3137254901960784 |
| subfield | 1 | 1 | 1.0 |
| topic | 1 | 1 | 1.0 |

## 14_final_alignment_matrix

| yago_type | soa_type | count |
| --- | --- | --- |
| creative_work_like | source | 11098 |
| organization_like | source | 275 |
| organization_like | publisher | 1553 |
| organization_like | funder | 1074 |
| organization_like | institution | 27169 |
| place_like | institution | 186 |
| creative_work_like | work | 273299 |
| person_like | author | 1656666 |
| creative_work_like | concept | 1477 |
| organism_like | concept | 46 |
| creative_work_like | keyword | 343 |
| intangible_like | concept | 3 |
| creative_work_like | topic | 1 |
| creative_work_like | subfield | 3 |
| creative_work_like | field | 1 |

## 15_top_ambiguous_labels

| label | frequency |
| --- | --- |
| introduction | 418728 |
| editorial board | 377108 |
| index | 277552 |
| preface | 200327 |
| table of contents | 195142 |
| editorial | 190264 |
| book reviews | 169495 |
| contents | 168392 |
| bibliography | 109726 |
| notes | 109199 |
| conclusion | 103994 |
| acknowledgments | 96066 |
| masthead | 93913 |
| reviews | 81787 |
| erratum | 78885 |
| foreword | 68743 |
| book review | 67360 |
| contributors | 64638 |
| books received | 60923 |
| einleitung | 59132 |

## 16_baseline_source_composition

| Source | Alignments | Share |
| --- | --- | --- |
| Strict proxy | 947748 | 0.5398458637836853 |
| Embedding-ranked | 807842 | 0.4601541362163147 |

## 17_baseline_type_composition

| Type | Alignments |
| --- | --- |
| author | 1546286 |
| work | 172389 |
| institution | 26490 |
| source | 7291 |
| publisher | 1322 |
| funder | 925 |
| concept | 724 |
| keyword | 160 |
| subfield | 2 |
| topic | 1 |

## 18_final_score_histogram

| Source group | ABC score bin | Count |
| --- | --- | --- |
| Strict proxy | 0.95 | 946496 |
| Strict proxy | 0.96 | 1842 |
| Strict proxy | 0.97 | 2583 |
| Strict proxy | 0.98 | 945 |
| Ranked ambiguous | 0.3 | 673 |
| Ranked ambiguous | 0.31 | 685 |
| Ranked ambiguous | 0.32 | 719 |
| Ranked ambiguous | 0.33 | 752 |
| Ranked ambiguous | 0.34 | 792 |
| Ranked ambiguous | 0.35 | 902 |
| Ranked ambiguous | 0.36 | 973 |
| Ranked ambiguous | 0.37 | 1007 |
| Ranked ambiguous | 0.38 | 1159 |
| Ranked ambiguous | 0.39 | 1271 |
| Ranked ambiguous | 0.4 | 1457 |
| Ranked ambiguous | 0.41 | 1716 |
| Ranked ambiguous | 0.42 | 2207 |
| Ranked ambiguous | 0.43 | 2958 |
| Ranked ambiguous | 0.44 | 3943 |
| Ranked ambiguous | 0.45 | 5585 |

## 19_entity_type_evolution

| System | Type | Alignments |
| --- | --- | --- |
| Baseline | Author | 1546286 |
| Baseline | Work | 172389 |
| Baseline | Institution | 26490 |
| Baseline | Source | 7291 |
| A+B | Author | 1657177 |
| A+B | Work | 276881 |
| A+B | Institution | 27361 |
| A+B | Source | 11392 |
| C | Author | 1643027 |
| C | Work | 245451 |
| C | Institution | 27045 |
| C | Source | 11815 |
| A+B+C | Author | 1656666 |
| A+B+C | Work | 273299 |
| A+B+C | Institution | 27355 |
| A+B+C | Source | 11373 |

## 20_evidence_correlations

| Cohort | Score 1 | Score 2 | Pearson r | Rows |
| --- | --- | --- | --- | --- |
| Accepted ambiguous | embedding_cosine | embedding_cosine | 1.0 | 24000 |
| Accepted ambiguous | embedding_cosine | profile_tfidf_score | 0.1322970592186618 | 24000 |
| Accepted ambiguous | embedding_cosine | neighbor_tfidf_score | -0.0631943824886129 | 24000 |
| Accepted ambiguous | embedding_cosine | abc_score | 0.9103990829683378 | 24000 |
| Accepted ambiguous | profile_tfidf_score | embedding_cosine | 0.1322970592186618 | 24000 |
| Accepted ambiguous | profile_tfidf_score | profile_tfidf_score | 1.0 | 24000 |
| Accepted ambiguous | profile_tfidf_score | neighbor_tfidf_score | -0.0087431927919547 | 24000 |
| Accepted ambiguous | profile_tfidf_score | abc_score | 0.5293578362985554 | 24000 |
| Accepted ambiguous | neighbor_tfidf_score | embedding_cosine | -0.0631943824886129 | 24000 |
| Accepted ambiguous | neighbor_tfidf_score | profile_tfidf_score | -0.0087431927919547 | 24000 |
| Accepted ambiguous | neighbor_tfidf_score | neighbor_tfidf_score | 1.0 | 24000 |
| Accepted ambiguous | neighbor_tfidf_score | abc_score | -0.0263930841527746 | 24000 |
| Accepted ambiguous | abc_score | embedding_cosine | 0.9103990829683378 | 24000 |
| Accepted ambiguous | abc_score | profile_tfidf_score | 0.5293578362985554 | 24000 |
| Accepted ambiguous | abc_score | neighbor_tfidf_score | -0.0263930841527746 | 24000 |
| Accepted ambiguous | abc_score | abc_score | 1.0 | 24000 |
| Threshold rejected | embedding_cosine | embedding_cosine | 1.0 | 3462 |
| Threshold rejected | embedding_cosine | profile_tfidf_score | -0.911102469999984 | 3462 |
| Threshold rejected | embedding_cosine | neighbor_tfidf_score | -0.0778437664422047 | 3462 |
| Threshold rejected | embedding_cosine | abc_score | 0.1005878525281405 | 3462 |

## 21_external_identifier_validation

| Type | Source | Final alignments | Externally checkable | QID agreement | Checkable share | Agreement rate |
| --- | --- | --- | --- | --- | --- | --- |
| concept | Strict proxy | 377 | 113 | 0 | 0.29973474801061 | 0.0 |
| concept | Ranked ambiguous | 1149 | 886 | 0 | 0.7711053089643168 | 0.0 |
| institution | Strict proxy | 26524 | 301 | 12 | 0.0113482129392248 | 0.0398671096345514 |
| institution | Ranked ambiguous | 831 | 28 | 0 | 0.0336943441636582 | 0.0 |
| funder | Strict proxy | 890 | 644 | 522 | 0.7235955056179775 | 0.8105590062111802 |
| funder | Ranked ambiguous | 184 | 137 | 110 | 0.7445652173913043 | 0.8029197080291971 |
| publisher | Strict proxy | 1294 | 1059 | 1034 | 0.8183925811437404 | 0.9763928234183192 |
| publisher | Ranked ambiguous | 259 | 184 | 140 | 0.7104247104247104 | 0.7608695652173914 |
| source | Strict proxy | 5209 | 3908 | 3737 | 0.7502399692839317 | 0.956243602865916 |
| source | Ranked ambiguous | 6164 | 3872 | 3456 | 0.6281635301752109 | 0.8925619834710744 |

## 22_rdf_processing_outcomes

| Dataset | Outcome | Statements | Processed statements | Share |
| --- | --- | --- | --- | --- |
| YAGO | Structural kept | 176573872 | 1784222285 | 0.0989640548066576 |
| YAGO | Literal/non-structural | 1607647674 | 1784222285 | 0.9010355310072814 |
| YAGO | Filtered subject | 739 | 1784222285 | 4.141860609032803e-07 |
| YAGO | Helper relation removed | 0 | 1784222285 | 0.0 |
| YAGO | Malformed | 0 | 1784222285 | 0.0 |
| SemOpenAlex | Structural kept | 9617571538 | 24420487935 | 0.3938320791787242 |
| SemOpenAlex | Literal/non-structural | 6015353175 | 24420487935 | 0.2463240370549131 |
| SemOpenAlex | Filtered subject | 8458693712 | 24420487935 | 0.3463769329472245 |
| SemOpenAlex | Helper relation removed | 328869510 | 24420487935 | 0.013466950819138 |
| SemOpenAlex | Malformed | 0 | 24420487935 | 0.0 |

## 23_target_catalog_coverage

| Type | SemOpenAlex items | Final alignments | Target-side coverage |
| --- | --- | --- | --- |
| concept | 65073 | 1526 | 0.0234505862646566 |
| institution | 111863 | 27355 | 0.2445401964903498 |
| source | 260808 | 11373 | 0.0436067912027238 |
| publisher | 10741 | 1553 | 0.1445861651615305 |
| funder | 32437 | 1074 | 0.033110336960878 |
| keyword | 4516 | 343 | 0.0759521700620017 |
| topic | 4516 | 1 | 0.0002214348981399 |
| subfield | 252 | 3 | 0.0119047619047619 |
| field | 26 | 1 | 0.0384615384615384 |
| domain | 4 | 0 | 0.0 |

## 24_bipartite_alignment_flows

| yago_type | soa_type | count |
| --- | --- | --- |
| creative_work_like | source | 11098 |
| organization_like | source | 275 |
| organization_like | publisher | 1553 |
| organization_like | funder | 1074 |
| organization_like | institution | 27169 |
| place_like | institution | 186 |
| creative_work_like | work | 273299 |
| person_like | author | 1656666 |
| creative_work_like | concept | 1477 |
| creative_work_like | keyword | 343 |

## 25_semopenalex_pbg_training

| Model | Epoch | Weighted loss | P10 | P90 | Partitions |
| --- | --- | --- | --- | --- | --- |
| TransE | 1 | 141.95812525994182 | 61.3409131802795 | 214.67122548335985 | 16384 |
| TransE | 2 | 55.66698872126822 | 21.929504529383436 | 73.68709972861187 | 16384 |
| TransE | 3 | 37.764302032195125 | 12.65226061872513 | 54.14731738100267 | 16384 |
| DistMult | 1 | 1.2937279995701012 | 0.7381502901655116 | 1.8704122116908497 | 16384 |
| DistMult | 2 | 0.5646193248110726 | 0.268118967281592 | 0.7505467567113822 | 16384 |
| DistMult | 3 | 0.4436456160370298 | 0.2098086379673073 | 0.6021075636101191 | 16384 |
| ComplEx | 1 | 1.298248434478988 | 0.736868293102663 | 1.8709064518823144 | 16384 |
| ComplEx | 2 | 0.5494974177813939 | 0.2591996086353647 | 0.7308883401259767 | 16384 |
| ComplEx | 3 | 0.4328176296197794 | 0.1978431664244083 | 0.5906928874761932 | 16384 |

## 26_neighbor_preservation

| dimension | group | evaluable_pairs | mean_jaccard | median_jaccard | pairs_with_shared_neighbor | shared_neighbor_rate | perfect_jaccard_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entity_type | author | 147263 | 0.0139567508060442 | 0.0 | 2320 | 0.0157541269701146 | 0.0125150241404833 |
| entity_type | concept | 920 | 0.0007246376811594 | 0.0 | 2 | 0.0021739130434782 | 0.0 |
| entity_type | field | 1 | 0.0 | 0.0 | 0 | 0.0 | 0.0 |
| entity_type | funder | 163 | 0.0 | 0.0 | 0 | 0.0 | 0.0 |
| entity_type | institution | 10957 | 0.01412967922153 | 0.0 | 506 | 0.0461805238660217 | 0.0075750661677466 |
| entity_type | keyword | 46 | 0.0 | 0.0 | 0 | 0.0 | 0.0 |
| entity_type | publisher | 341 | 0.0068565842759391 | 0.0 | 6 | 0.0175953079178885 | 0.002932551319648 |
| entity_type | source | 435 | 0.0 | 0.0 | 0 | 0.0 | 0.0 |
| entity_type | subfield | 1 | 0.0 | 0.0 | 0 | 0.0 | 0.0 |
| entity_type | topic | 1 | 0.0 | 0.0 | 0 | 0.0 | 0.0 |
| entity_type | work | 46900 | 0.0415767844451213 | 0.0 | 2106 | 0.0449040511727078 | 0.0387846481876332 |
| source_group | Ranked ambiguous | 100685 | 0.0056589935035368 | 0.0 | 672 | 0.0066742811739583 | 0.0049759149823707 |
| source_group | Strict proxy | 106343 | 0.0337898317769682 | 0.0 | 4268 | 0.0401342824633497 | 0.0305144673368251 |
| overall | All | 207028 | 0.0201088154334763 | 0.0 | 4940 | 0.0238615066561044 | 0.018094170836795 |

## 27_bridge_topology

| state | nodes | within_graph_edges | identity_bridges | total_edges | connected_components | largest_component_nodes | mean_component_size |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Before identity bridges | 3946388 | 166088 | 0 | 166088 | 3784620 | 16531 | 1.0427435251095225 |
| After identity bridges | 3946388 | 166088 | 1973194 | 2139282 | 1814573 | 102624 | 2.174830111546904 |

## 28_formal_schema_inventory

| Dataset | Metric | Value |
| --- | --- | --- |
| YAGO | Node shapes | 40 |
| YAGO | Declared classes | 40 |
| YAGO | Declared object properties | 0 |
| YAGO | Declared datatype properties | 0 |
| YAGO | Declared annotation properties | 0 |
| YAGO | Unique constrained predicates | 106 |
| YAGO | SHACL object-range predicates | 62 |
| YAGO | SHACL datatype-range predicates | 44 |
| YAGO | SHACL mixed-range predicates | 0 |
| YAGO | Shape-property constraints | 141 |
| YAGO | Predicate namespaces reused | 3 |
| YAGO | hierarchy_nodes | 132878 |
| YAGO | subclass_edges | 166360 |
| YAGO | root_classes | 1 |
| YAGO | maximum_observed_depth | 19 |
| SemOpenAlex | Node shapes | 21 |
| SemOpenAlex | Declared classes | 21 |
| SemOpenAlex | Declared object properties | 33 |
| SemOpenAlex | Declared datatype properties | 81 |
| SemOpenAlex | Declared annotation properties | 0 |

## 29_semantic_predicate_signatures

| Dataset | Domain URI | Domain | Predicate URI | Predicate | Range URI | Range | Property kind | Predicate namespace |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| YAGO | http://schema.org/Book | Book | http://schema.org/numberOfPages | numberOfPages | http://www.w3.org/2001/XMLSchema#decimal | decimal | datatype | http://schema.org/ |
| YAGO | http://schema.org/Book | Book | http://schema.org/illustrator | illustrator | http://schema.org/Person | Person | object | http://schema.org/ |
| YAGO | http://schema.org/Book | Book | http://schema.org/editor | editor | http://schema.org/Person | Person | object | http://schema.org/ |
| YAGO | http://schema.org/Book | Book | http://schema.org/publisher | publisher | http://schema.org/Organization | Organization | object | http://schema.org/ |
| YAGO | http://schema.org/Book | Book | http://schema.org/publisher | publisher | http://schema.org/Person | Person | object | http://schema.org/ |
| YAGO | http://schema.org/Book | Book | http://schema.org/isbn | isbn | http://www.w3.org/2001/XMLSchema#string | string | datatype | http://schema.org/ |
| YAGO | http://yago-knowledge.org/resource/Academic | Academic | http://yago-knowledge.org/resource/doctoralAdvisor | doctoralAdvisor | http://schema.org/Person | Person | object | http://yago-knowledge.org/resource/ |
| YAGO | http://yago-knowledge.org/resource/Academic | Academic | http://yago-knowledge.org/resource/studentOf | studentOf | http://schema.org/Person | Person | object | http://yago-knowledge.org/resource/ |
| YAGO | http://schema.org/Taxon | Taxon | http://schema.org/parentTaxon | parentTaxon | http://schema.org/Taxon | Taxon | object | http://schema.org/ |
| YAGO | http://schema.org/Taxon | Taxon | http://yago-knowledge.org/resource/consumes | consumes | http://schema.org/Taxon | Taxon | object | http://yago-knowledge.org/resource/ |
| YAGO | http://schema.org/MusicGroup | MusicGroup | http://yago-knowledge.org/resource/influencedBy | influencedBy | http://schema.org/Thing | Thing | object | http://yago-knowledge.org/resource/ |
| YAGO | http://schema.org/MusicGroup | MusicGroup | http://schema.org/recordLabel | recordLabel | http://schema.org/Organization | Organization | object | http://schema.org/ |
| YAGO | http://schema.org/Product | Product | http://schema.org/material | material | http://schema.org/Product | Product | object | http://schema.org/ |
| YAGO | http://schema.org/Product | Product | http://schema.org/dateCreated | dateCreated | http://www.w3.org/2001/XMLSchema#dateTime | dateTime | datatype | http://schema.org/ |
| YAGO | http://schema.org/Product | Product | http://schema.org/dateCreated | dateCreated | http://www.w3.org/2001/XMLSchema#date | date | datatype | http://schema.org/ |
| YAGO | http://schema.org/Product | Product | http://schema.org/dateCreated | dateCreated | http://www.w3.org/2001/XMLSchema#gYearMonth | gYearMonth | datatype | http://schema.org/ |
| YAGO | http://schema.org/Product | Product | http://schema.org/dateCreated | dateCreated | http://www.w3.org/2001/XMLSchema#gYear | gYear | datatype | http://schema.org/ |
| YAGO | http://schema.org/Product | Product | http://schema.org/manufacturer | manufacturer | http://schema.org/Corporation | Corporation | object | http://schema.org/ |
| YAGO | http://schema.org/Product | Product | http://schema.org/gtin | gtin | http://www.w3.org/2001/XMLSchema#string | string | datatype | http://schema.org/ |
| YAGO | http://schema.org/Product | Product | http://schema.org/award | award | http://yago-knowledge.org/resource/Award | Award | object | http://schema.org/ |

## 30_ontology_source_provenance

| Source | Path | SHA-256 |
| --- | --- | --- |
| YAGO schema | 01_raw/yago/yago-schema.ttl | 9f1a9290d7cae5610c145bdb1c73928afb3d598e06604ced5a1b612bd704ee93 |
| YAGO taxonomy | 01_raw/yago/yago-taxonomy.ttl | a2090f018039c63e2290c59484b73a322fe8287ab2f8a0f394b211e69209c126 |
| SemOpenAlex ontology | 01_raw/semopenalex/semopenalex-ontology.ttl | 9557078a1fdb75a5aeafd94d1192f752dc5af2cd6912fd58ab5b7434f4c85e29 |

## 31_confidence_by_entity_type

| Entity type | Ranked ambiguous alignments | Mean ABC score | P10 | Median | P90 | Minimum | Maximum |
| --- | --- | --- | --- | --- | --- | --- | --- |
| author | 890479 | 0.5800809264183044 | 0.5156893730163574 | 0.5823526382446289 | 0.6422684788703918 | 0.3000058233737945 | 0.8046283721923828 |
| concept | 1149 | 0.5046626925468445 | 0.4429075121879577 | 0.5127885937690735 | 0.5617634654045105 | 0.3018670976161957 | 0.6276364922523499 |
| field | 1 | 0.5356824398040771 | 0.5356824398040771 | 0.5356824398040771 | 0.5356824398040771 | 0.5356824398040771 | 0.5356824398040771 |
| funder | 184 | 0.4752902686595917 | 0.3432400822639465 | 0.4861801266670227 | 0.5676940083503723 | 0.3067602813243866 | 0.6422274708747864 |
| institution | 831 | 0.5026953220367432 | 0.4639735817909241 | 0.4956008493900299 | 0.5650354027748108 | 0.3000384569168091 | 0.64144366979599 |
| keyword | 327 | 0.5329143404960632 | 0.4804444015026092 | 0.5329366326332092 | 0.5942594408988953 | 0.304110050201416 | 0.6571779251098633 |
| publisher | 259 | 0.5145778656005859 | 0.4651413559913635 | 0.5118140578269958 | 0.5800893306732178 | 0.301299124956131 | 0.6829485893249512 |
| source | 6164 | 0.5733898878097534 | 0.5081289410591125 | 0.5734012126922607 | 0.6470644474029541 | 0.3001255393028259 | 0.7846627235412598 |
| subfield | 2 | 0.5945816040039062 | 0.5832233428955078 | 0.5945816040039062 | 0.6059398055076599 | 0.5803837776184082 | 0.6087793707847595 |
| work | 121932 | 0.4991678893566131 | 0.4476907849311828 | 0.5033711194992065 | 0.5533175468444824 | 0.300013929605484 | 0.6925653219223022 |

## 32_rdf_export_composition

| Group | Triples per alignment | Total triples | Share | Contents |
| --- | --- | --- | --- | --- |
| Direct identity assertion | 1 | 1973194 | 0.0769230769230769 | owl:sameAs |
| Standard reification structure | 5 | 9865970 | 0.3846153846153846 | rdf:Statement + kg:Alignment types; rdf:subject/predicate/object |
| Numerical evidence | 4 | 7892776 | 0.3076923076923077 | embedding, profile, neighbor, and ABC scores |
| Categorical metadata | 3 | 5919582 | 0.2307692307692307 | SemOpenAlex type, selection source, confidence tier |

## 33_relation_rank_frequency

| Dataset | Rank | Predicate | Predicate URI | Held-out occurrences | Share | Cumulative share |
| --- | --- | --- | --- | --- | --- | --- |
| YAGO | 1 | type | http://www.w3.org/1999/02/22-rdf-syntax-ns#type | 52604 | 0.2979147552867353 | 0.2979147552867353 |
| YAGO | 2 | sameAs | http://www.w3.org/2002/07/owl#sameAs | 49557 | 0.280658534099018 | 0.5785732893857534 |
| YAGO | 3 | location | http://schema.org/location | 22517 | 0.1275216056724093 | 0.7060948950581627 |
| YAGO | 4 | gender | http://schema.org/gender | 8697 | 0.0492541370756736 | 0.7553490321338363 |
| YAGO | 5 | author | http://schema.org/author | 4020 | 0.0227666587379795 | 0.7781156908718159 |
| YAGO | 6 | parentTaxon | http://schema.org/parentTaxon | 3660 | 0.0207278534778619 | 0.7988435443496779 |
| YAGO | 7 | inLanguage | http://schema.org/inLanguage | 3436 | 0.0194592635382332 | 0.8183028078879111 |
| YAGO | 8 | nationality | http://schema.org/nationality | 3258 | 0.018451187604064 | 0.8367539954919752 |
| YAGO | 9 | birthPlace | http://schema.org/birthPlace | 3201 | 0.018128376771212 | 0.8548823722631872 |
| YAGO | 10 | about | http://schema.org/about | 2950 | 0.0167068764370745 | 0.8715892487002618 |
| YAGO | 11 | knowsLanguage | http://schema.org/knowsLanguage | 2541 | 0.0143905671276631 | 0.885979815827925 |
| YAGO | 12 | alumniOf | http://schema.org/alumniOf | 2457 | 0.0139148459003024 | 0.8998946617282274 |
| YAGO | 13 | memberOf | http://schema.org/memberOf | 2453 | 0.0138921925085233 | 0.9137868542367508 |
| YAGO | 14 | children | http://schema.org/children | 1628 | 0.0092199304540872 | 0.923006784690838 |
| YAGO | 15 | worksFor | http://schema.org/worksFor | 1573 | 0.0089084463171248 | 0.9319152310079628 |
| YAGO | 16 | material | http://schema.org/material | 1390 | 0.0078720536432317 | 0.9397872846511944 |
| YAGO | 17 | actor | http://schema.org/actor | 1332 | 0.007543579462435 | 0.9473308641136295 |
| YAGO | 18 | award | http://schema.org/award | 1293 | 0.0073227088925889 | 0.9546535730062184 |
| YAGO | 19 | deathPlace | http://schema.org/deathPlace | 1280 | 0.0072490853693069 | 0.9619026583755254 |
| YAGO | 20 | neighbors | http://yago-knowledge.org/resource/neighbors | 836 | 0.0047345588818285 | 0.966637217257354 |

## 34_degree_ccdf

| Dataset | Degree threshold | Nodes at degree | Nodes with degree at least threshold | CCDF |
| --- | --- | --- | --- | --- |
| YAGO held-out | 1 | 256464 | 263202 | 1.0 |
| YAGO held-out | 2 | 3278 | 6738 | 0.0256001094216609 |
| YAGO held-out | 3 | 1120 | 3460 | 0.0131457967644622 |
| YAGO held-out | 4 | 575 | 2340 | 0.0088905099505322 |
| YAGO held-out | 5 | 341 | 1765 | 0.0067058760951664 |
| YAGO held-out | 6 | 211 | 1424 | 0.0054102932348538 |
| YAGO held-out | 7 | 145 | 1213 | 0.0046086275940152 |
| YAGO held-out | 8 | 110 | 1068 | 0.0040577199261403 |
| YAGO held-out | 9 | 84 | 958 | 0.0036397899712008 |
| YAGO held-out | 10 | 78 | 874 | 0.003320643460156 |
| YAGO held-out | 11 | 62 | 796 | 0.0030242931284716 |
| YAGO held-out | 12 | 35 | 734 | 0.0027887326084148 |
| YAGO held-out | 13 | 37 | 699 | 0.0026557548954795 |
| YAGO held-out | 14 | 49 | 662 | 0.0025151784560907 |
| YAGO held-out | 15 | 35 | 613 | 0.0023290096579813 |
| YAGO held-out | 16 | 24 | 578 | 0.002196031945046 |
| YAGO held-out | 17 | 37 | 554 | 0.0021048472276046 |
| YAGO held-out | 18 | 22 | 517 | 0.0019642707882158 |
| YAGO held-out | 19 | 28 | 495 | 0.0018806847972279 |
| YAGO held-out | 20 | 11 | 467 | 0.0017743026268797 |

## 35_predicate_namespace_composition

| Dataset | Predicate namespace | Held-out occurrences | Share |
| --- | --- | --- | --- |
| YAGO | schema.org | 70772 | 0.4008064607473354 |
| YAGO | RDF | 52604 | 0.2979147552867353 |
| YAGO | OWL | 49557 | 0.280658534099018 |
| YAGO | YAGO | 3475 | 0.0196801341080793 |
| YAGO | RDFS | 166 | 0.0009401157588319 |
| SemOpenAlex | SemOpenAlex ontology | 5689429 | 0.591523849744933 |
| SemOpenAlex | CiTO | 2613828 | 0.2717569023413595 |
| SemOpenAlex | Dublin Core | 699585 | 0.0727351044232749 |
| SemOpenAlex | RDF | 367809 | 0.0382407084526116 |
| SemOpenAlex | OWL | 193685 | 0.0201372223535696 |
| SemOpenAlex | W3C ORG | 51873 | 0.0053931803451311 |
| SemOpenAlex | SKOS | 1828 | 0.0001900552054228 |
| SemOpenAlex | DBpedia | 113 | 1.1748489175482712e-05 |
| SemOpenAlex | RDFS | 108 | 1.122864452170029e-05 |

## 36_predicate_entropy

| Dataset | Observed predicates | Shannon entropy (bits) | Maximum entropy (bits) | Normalized entropy | Effective predicates (2^H) | Gini coefficient |
| --- | --- | --- | --- | --- | --- | --- |
| YAGO | 61 | 3.234174868227546 | 5.930737337562887 | 0.5453242462355555 | 9.409870498141848 | 0.8638371466233356 |
| SemOpenAlex | 30 | 3.4480145142180163 | 4.906890595608519 | 0.7026882802938095 | 10.913292471544649 | 0.7217129685368529 |

## 37_pbg_partitioning_scale

| Dataset | Entity partitions | Partition-pair buckets | Entities | Train triples | Embedding dimension | Batch size | Epochs | Mean entities per partition | Arithmetic mean triples per partition-pair bucket | Checkpoint partition files | Median checkpoint GiB per partition | Minimum checkpoint GiB | Maximum checkpoint GiB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| YAGO | 32 | 1024 | 99313458 | 176220725 | 200 | 100000 | 5 | 3103545.5625 | 172090.5517578125 | 32 | 2.323916400782764 | 2.3239156557247043 | 2.323916400782764 |
| SemOpenAlex | 128 | 16384 | 1936550634 | 9598336260 | 200 | 200000 | 3 | 15129301.828125 | 585835.9533691406 | 128 | 11.328588615171611 | 11.328587870113552 | 11.328588615171611 |

## 38_link_prediction_rank_bands

| Dataset | Model | Rank band | Share | Test triples |
| --- | --- | --- | --- | --- |
| YAGO | TransE | Rank = 1 | 0.334888 | 176574 |
| YAGO | TransE | Ranks 2–10 | 0.282267 | 176574 |
| YAGO | TransE | Ranks 11–50 | 0.368474 | 176574 |
| YAGO | TransE | Rank > 50 | 0.014371 | 176574 |
| YAGO | DistMult | Rank = 1 | 0.418131 | 176574 |
| YAGO | DistMult | Ranks 2–10 | 0.201816 | 176574 |
| YAGO | DistMult | Ranks 11–50 | 0.350397 | 176574 |
| YAGO | DistMult | Rank > 50 | 0.029656 | 176574 |
| YAGO | ComplEx | Rank = 1 | 0.400654 | 176574 |
| YAGO | ComplEx | Ranks 2–10 | 0.200165 | 176574 |
| YAGO | ComplEx | Ranks 11–50 | 0.360693 | 176574 |
| YAGO | ComplEx | Rank > 50 | 0.038488 | 176574 |
| SemOpenAlex | TransE | Rank = 1 | 0.72418 | 50000 |
| SemOpenAlex | TransE | Ranks 2–10 | 0.17598 | 50000 |
| SemOpenAlex | TransE | Ranks 11–50 | 0.0961 | 50000 |
| SemOpenAlex | TransE | Rank > 50 | 0.00374 | 50000 |
| SemOpenAlex | DistMult | Rank = 1 | 0.79984 | 50000 |
| SemOpenAlex | DistMult | Ranks 2–10 | 0.10687 | 50000 |
| SemOpenAlex | DistMult | Ranks 11–50 | 0.09282 | 50000 |
| SemOpenAlex | DistMult | Rank > 50 | 0.00047 | 50000 |
