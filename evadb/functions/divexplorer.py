from typing import List, Optional

from divexplorer.FP_DivergenceExplorer import FP_DivergenceExplorer
from divexplorer.FP_Divergence import FP_Divergence
import pandas as pd

from evadb.catalog.catalog_type import NdArrayType
from evadb.functions.abstract.abstract_function import AbstractFunction
from evadb.functions.decorators.decorators import forward, setup
from evadb.functions.decorators.io_descriptors.data_types import PandasDataframe


class DivExplorer(AbstractFunction):
    @setup(cacheable=True, function_type="FeatureExtraction", batchable=True)
    def setup(
        self,
        min_support: float = 0.1,
        max_len: int = 3,
        # metrics: List[str] = "fpr",
        metric: str = "d_fpr",
        ignore_cols: List[str] = None,
        th_redundancy: Optional[float] = None,
        top_k: Optional[int] = None,
    ):
        self.min_support = min_support
        self.max_len = max_len
        self.metric = metric
        self.ignore_cols = ignore_cols
        self.th_redundancy = th_redundancy
        self.top_k = top_k

    @property
    def name(self) -> str:
        return "DivExplorer"

    @forward(
        input_signatures=[
            PandasDataframe(
                columns=["class", "predicted"],
                column_types=[
                    NdArrayType.UINT8,
                    NdArrayType.UINT8,
                ],
                column_shapes=[(None,), (None,)]
            )
        ],
        output_signatures=[
            PandasDataframe(
                columns=["itemsets", "support", "support_count", "fpr", "d_fpr", "t_value_fp"],
                column_types=[
                    NdArrayType.STR,
                    NdArrayType.FLOAT32,
                    NdArrayType.UINT8,
                    NdArrayType.FLOAT32,
                    NdArrayType.FLOAT32,
                    NdArrayType.FLOAT32,
                ],
                column_shapes=[(None,), (None,), (None,), (None,), (None,), (None,)]
            )
        ],
    )
    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        fp_diver = FP_DivergenceExplorer(
            df, true_class_name="class", 
            predicted_class_name="predicted", class_map={'N': 0, 'P': 1}
        )
        result_divexplore = fp_diver.getFrequentPatternDivergence(
            min_support=self.min_support, metrics=[self.metric], # TODO: Add max_len to DivExplorer, and multiple metrics
        )
        if self.top_k is not None:
            fp_divergence_metric = FP_Divergence(
                result_divexplore, self.metric
            )
            topK_df_metric = fp_divergence_metric.getDivergenceTopKDf(
                K=self.top_k, th_redundancy=self.th_redundancy
            )
            return topK_df_metric

        return result_divexplore


        # return df
