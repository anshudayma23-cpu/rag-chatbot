import asyncio
import sys
import os
import argparse
from datetime import datetime

# Path setup: Add the current working directory (project root) to sys.path
sys.path.append(os.getcwd())

print(f"--- Pipeline Debug: CWD={os.getcwd()} Path={sys.path[:3]} ---")

try:
    from src.utils.logger import setup_logger
    from src.ingestion.scraper import GrowwScraper
    from src.ingestion.processor import DataProcessor
except ImportError as e:
    print(f"--- Pipeline Debug: Import Error: {e} ---")
    # Immediate fallback attempt
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
    from src.utils.logger import setup_logger
    from src.ingestion.scraper import GrowwScraper
    from src.ingestion.processor import DataProcessor

async def run_pipeline(log_to_file: bool = True):
    """Orchestrates the ingestion pipeline."""
    logger = setup_logger(name="ingestion", log_to_file=log_to_file)
    
    logger.info("=" * 60)
    logger.info("Starting Ingestion Pipeline")
    logger.info("=" * 60)
    
    try:
        logger.info("--- Phase 1: Ingestion & Scraping ---")
        scraper = GrowwScraper()
        raw_data = await scraper.run()
        
        if not raw_data:
            logger.error("No data scraped. Aborting pipeline.")
            return

        logger.info(f"Successfully Scraped {len(raw_data)} Funds")
        
        logger.info("--- Phase 2: Chunking & Embedding ---")
        processor = DataProcessor()
        processor.process_data(raw_data)
        
        logger.info("=" * 60)
        logger.info("Ingestion Pipeline Complete Successfully")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HDFC Mutual Fund RAG Ingestion Pipeline")
    parser.add_argument("--no-file-log", action="store_true", help="Disable logging to file")
    args = parser.parse_args()
    
    asyncio.run(run_pipeline(log_to_file=not args.no_file_log))
