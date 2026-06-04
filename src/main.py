from logger import setup_logger
from utils import load_config
from etl import ETLPipeline


logger = setup_logger()

config = load_config()

logger.info(
    "CloudForge Pipeline Started Successfully"
)

# Initialize ETL pipeline
pipeline = ETLPipeline(
    config=config,
    logger=logger
)

# Run ETL process
result = pipeline.run_pipeline(
    "data/sales_data.csv"
)

logger.info(f"Pipeline Result: {result}")
