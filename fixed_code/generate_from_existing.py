import os
import json
import sys
import logging
from datetime import datetime

# Configure logging
def setup_logger():
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create a logger
    logger = logging.getLogger('question_generator')
    logger.setLevel(logging.INFO)
    
    # Create handlers
    # File handler - logs to file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_handler = logging.FileHandler(f'logs/question_generation_{timestamp}.log')
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatters and add it to handlers
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(log_format)
    console_handler.setFormatter(log_format)
    
    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Add the directory containing dataGen.py to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import functions from dataGen.py
from dataGen import (
    load_docs_from_dir,
    generate_questions_for_samples,
    save_questions_with_topics
)

def generate_questions_from_existing_data(
    topic_combinations_file="output/topic_combinations.json",
    document_extractions_file="output/document_extractions.json",
    docs_dir="docs/",
    output_file="output/questions_from_existing.json",
    max_samples=5
):
    """
    Generate questions using existing topic combinations and document extractions.
    
    Args:
        topic_combinations_file: Path to the saved topic combinations JSON file
        document_extractions_file: Path to the saved document extractions JSON file
        docs_dir: Directory containing the original PDF documents
        output_file: Path to save the generated questions
        max_samples: Maximum number of topic combinations to use
    """
    # Setup logger
    logger = setup_logger()
    logger.info("Starting question generation process")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    logger.info(f"Loading topic combinations from {topic_combinations_file}")
    try:
        with open(topic_combinations_file, 'r') as f:
            combos = json.load(f)
        logger.info(f"Successfully loaded {len(combos)} topic combinations")
    except Exception as e:
        logger.error(f"Error loading topic combinations: {e}")
        return
    
    logger.info(f"Loading document extractions from {document_extractions_file}")
    try:
        with open(document_extractions_file, 'r') as f:
            extractions = json.load(f)
        logger.info(f"Successfully loaded extractions for {len(extractions)} documents")
    except Exception as e:
        logger.error(f"Error loading document extractions: {e}")
        return
    
    # Load the original documents
    logger.info(f"Loading original documents from {docs_dir}")
    docs, filenames = load_docs_from_dir(docs_dir)
    
    if len(docs) == 0:
        logger.error("No documents found. Please check the docs directory.")
        return
    
    logger.info(f"Successfully loaded {len(docs)} documents")
    
    # Create a mapping from filenames to document indices
    filename_to_index = {filename: i for i, filename in enumerate(filenames)}
    
    # Limit the number of combinations to process
    if max_samples and max_samples < len(combos):
        logger.info(f"Using only the first {max_samples} topic combinations")
        combos = combos[:max_samples]
    
    # Generate questions
    logger.info("Starting question generation")
    q_outputs = generate_questions_for_samples(combos, docs, extractions)
    logger.info(f"Generated questions for {len(q_outputs)} combinations")
    
    # Save questions
    logger.info(f"Saving questions to {output_file}")
    save_questions_with_topics(q_outputs, output_file)
    
    # Log results
    logger.info("\n===== GENERATED QUESTIONS =====")
    for idx, out in enumerate(q_outputs, 1):
        logger.info(f"\nSample {idx}:")
        logger.info(f"Topics: {out['topics']}")
        logger.info(f"Key Concepts: {out['key_concepts']}")
        logger.info(f"Reference Files: {out['reference_files']}")
        logger.info("Questions:")
        for q in out['questions']:
            logger.info(f" - {q}")
    
    logger.info(f"\nResults saved to {output_file}")

if __name__ == "__main__":
    # Use default file paths or override with command line arguments
    topic_combinations_file = "output/topic_combinations.json"
    document_extractions_file = "output/document_extractions.json"
    docs_dir = "docs/"
    output_file = "output/questions_from_existing.json"
    max_samples = 5  # Limit to 5 samples for faster processing
    
    # Allow command line overrides
    if len(sys.argv) > 1:
        topic_combinations_file = sys.argv[1]
    if len(sys.argv) > 2:
        document_extractions_file = sys.argv[2]
    if len(sys.argv) > 3:
        docs_dir = sys.argv[3]
    if len(sys.argv) > 4:
        output_file = sys.argv[4]
    if len(sys.argv) > 5:
        max_samples = int(sys.argv[5])
    
    generate_questions_from_existing_data(
        topic_combinations_file,
        document_extractions_file,
        docs_dir,
        output_file,
        max_samples
    ) 