import os
import glob
import json
import math
import random
import re
import logging
from datetime import datetime
from collections import Counter
import networkx as nx
import pdfplumber
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# Configure logging
def setup_logger():
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create a logger
    logger = logging.getLogger('data_generator')
    logger.setLevel(logging.INFO)
    
    # Create handlers
    # File handler - logs to file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_handler = logging.FileHandler(f'logs/data_generation_{timestamp}.log')
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

# Set up logger
logger = setup_logger()

# Set the OpenAI API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# -- Document Loading ------------------------------------------------------

def load_docs_from_dir(dir_path):
    """
    Load all .pdf files from a directory and extract their full text.
    Returns a list of strings, one per PDF.
    """
    docs = []
    filenames = []
    logger.info(f"Loading documents from directory: {dir_path}")
    
    for filepath in glob.glob(os.path.join(dir_path, '*.pdf')):
        try:
            text_pages = []
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    text_pages.append(page.extract_text() or "")
            full_text = "\n".join(text_pages)
            docs.append(full_text)
            filenames.append(os.path.basename(filepath))
            logger.info(f"Successfully loaded document: {os.path.basename(filepath)}")
        except Exception as e:
            logger.error(f"Warning: could not load {filepath}: {e}")
    return docs, filenames

# -- 1. Extract topics and key concepts -----------------------------------

def extract_json_from_text(text):
    """Helper function to extract JSON content from markdown code blocks or raw text"""
    # Try to extract JSON from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()
    
    # If no code blocks, try to find JSON-like structures
    json_match = re.search(r'(\{.*\})', text, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()
    
    # Return original text if no JSON structure found
    return text

def extract_concepts_from_docs(doc_texts, filenames, model="gpt-4o"):  
    """
    Call OpenAI API to extract topics and key concepts from each document.
    Returns list of dicts with keys 'topics' and 'key_concepts'.
    """
    extractions = []
    for i, text in enumerate(doc_texts):
        filename = filenames[i] if i < len(filenames) else f"doc_{i}"
        logger.info(f"Extracting concepts from document: {filename}")
        
        prompt = (
            "Extract high-level topics and key concepts from the following document. "
            f"Return JSON with keys 'topics' and 'key_concepts'.\n\n{text}"
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert summarizer. Return your response as a JSON object with 'topics' and 'key_concepts' as arrays."},
                {"role": "user", "content": prompt}
            ],
        )
        
        output = response.choices[0].message.content
        logger.info(f"Raw LLM output for {filename}: {output}")
        
        try:
            # Clean and extract JSON from the output
            json_str = extract_json_from_text(output)
            data = json.loads(json_str)
            
            # Ensure we have the expected keys
            if "topics" in data and "key_concepts" in data:
                extraction = {
                    "filename": filename,
                    "topics": data["topics"],
                    "key_concepts": data["key_concepts"]
                }
                extractions.append(extraction)
                logger.info(f"Successfully extracted {len(data['topics'])} topics and {len(data['key_concepts'])} key concepts from {filename}")
            else:
                logger.warning(f"Parsed JSON doesn't have expected keys: {data.keys()}")
                extractions.append({
                    "filename": filename,
                    "topics": [], 
                    "key_concepts": []
                })
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON for {filename}: {e}")
            extractions.append({
                "filename": filename,
                "topics": [], 
                "key_concepts": []
            })
    
    return extractions

# -- 2. Construct the concept graph ----------------------------------------

def build_concept_graph(extractions, eps=1e-6):
    """
    Build a unified graph G where nodes are topics + key concepts and
    edges weighted by log(freq+eps) based on co-occurrence in docs.
    Returns: G (nx.Graph), topic_nodes, kc_nodes
    """
    logger.info("Building concept graph...")
    freq = Counter()
    all_topics, all_kcs = set(), set()

    for ex in extractions:
        nodes = ex["topics"] + ex["key_concepts"]
        for i in range(len(nodes)):
            for j in range(i+1, len(nodes)):
                u, v = sorted((nodes[i], nodes[j]))
                freq[(u, v)] += 1
        all_topics.update(ex["topics"])
        all_kcs.update(ex["key_concepts"])

    G = nx.Graph()
    for (u, v), f in freq.items():
        weight = math.log(f + eps)
        G.add_edge(u, v, weight=weight)

    logger.info(f"Graph built with {len(all_topics)} topics and {len(all_kcs)} key concepts")
    return G, all_topics, all_kcs

# -- Helpers for sampling --------------------------------------------------

def softmax(weights):
    exps = [math.exp(w) for w in weights]
    s = sum(exps) or 1.0
    return [e/s for e in exps]

def random_walk(G, start, steps):
    """
    Random walk on graph G for given steps from 'start',
    with transition probabilities via softmax over edge weights.
    """
    path = [start]
    current = start
    for _ in range(steps):
        nbrs = list(G[current])
        if not nbrs:
            break
        weights = [G[current][n]['weight'] for n in nbrs]
        probs = softmax(weights)
        current = random.choices(nbrs, probs)[0]
        path.append(current)
    return path

# -- 3. Concept combination sampling ---------------------------------------

def sample_concept_combinations(
    G, topic_nodes, kc_nodes,
    num_samples=100,
    topic_walk_steps=(1, 2),
    kc_walk_steps=(3, 4)
):
    """
    Generate sampled sets of topics and key concepts via multi-stage random walks.
    Returns list of dicts: {'topics': set, 'key_concepts': set}
    """
    logger.info("Sampling concept combinations...")
    
    # Safety check
    if not topic_nodes:
        logger.error("No topics found. Cannot sample combinations.")
        return []
        
    G_topic = G.subgraph(topic_nodes)
    G_topic_kc = G.subgraph(topic_nodes | kc_nodes)
    G_kc = G.subgraph(kc_nodes)
    samples = []

    topics_list = list(topic_nodes)
    logger.info(f"Sampling from {len(topics_list)} topics")
    
    for i in range(num_samples):
        t0 = random.choice(topics_list)
        t_steps = random.choice(topic_walk_steps)
        topic_path = random_walk(G_topic, t0, t_steps)
        sampled_topics = set(topic_path)

        kc_cands = [nbr for t in sampled_topics for nbr in G_topic_kc[t] if nbr in kc_nodes]
        if kc_cands:
            k0 = random.choice(kc_cands)
            k_steps = random.choice(kc_walk_steps)
            kc_path = random_walk(G_kc, k0, k_steps)
            sampled_kcs = set(kc_path)
        else:
            sampled_kcs = set()

        samples.append({
            "topics": list(sampled_topics),
            "key_concepts": list(sampled_kcs)
        })
        logger.info(f"Generated sample {i+1}/{num_samples}")
    
    return samples

# -- 4. Question generation ------------------------------------------------

def generate_questions_for_samples(combos, docs, extractions, model="gpt-4o"):  
    """
    For each sampled combo, pick two docs via Jaccard on concept sets,
    then call LLM to generate questions.
    Returns list of dicts: {'sample': combo, 'questions': [...]}.
    """
    logger.info("Generating questions for samples...")
    doc_concepts = [set(ex['topics'] + ex['key_concepts']) for ex in extractions]
    results = []

    for i, combo in enumerate(combos):
        logger.info(f"Processing combination {i+1}/{len(combos)}")
        combo_id = f"combo_{i+1}"
        kg = set(combo['topics']) | set(combo['key_concepts'])
        sims = []
        for idx, dc in enumerate(doc_concepts):
            inter = kg & dc
            union = kg | dc
            sims.append((len(inter) / (len(union) or 1), idx))
        sims.sort(reverse=True)
        top_idxs = [i for _, i in sims[:2]]
        refs = [docs[i] for i in top_idxs]
        ref_files = [extractions[i]["filename"] for i in top_idxs]

        prompt = (
            f"Generate a set of questions based on the following:\n"
            f"Topics: {combo['topics']}\n"
            f"Key Concepts: {combo['key_concepts']}\n"
            f"Reference Doc 1:\n{refs[0]}\n"
        )
        if len(refs) > 1:
            prompt += f"Reference Doc 2:\n{refs[1]}\n"
        prompt += "Return a JSON array of questions."

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful question generator. Return your response as a JSON array of questions."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content
        logger.info(f"Raw LLM output for combination {i+1}: {content}")
        
        try:
            # Clean and extract JSON from the output
            json_str = extract_json_from_text(content)
            questions = json.loads(json_str)
            if not isinstance(questions, list):
                # If the output is an object with a questions key
                if isinstance(questions, dict) and "questions" in questions:
                    questions = questions["questions"]
                else:
                    questions = [str(questions)]
            logger.info(f"Successfully parsed {len(questions)} questions for combination {i+1}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON for combination {i+1}: {e}")
            questions = [content]

        results.append({
            "id": combo_id,
            "topics": combo['topics'],
            "key_concepts": combo['key_concepts'],
            "reference_files": ref_files,
            "questions": questions
        })

    return results

# -- Save outputs to files ------------------------------------------------

def save_extractions(extractions, output_file="document_extractions.json"):
    """Save the extracted topics and key concepts for each document"""
    logger.info(f"Saving extractions to {output_file}")
    # Ensure the extractions are serializable (convert sets to lists)
    serializable_extractions = []
    for ex in extractions:
        serializable_extractions.append({
            "filename": ex["filename"],
            "topics": list(ex["topics"]),
            "key_concepts": list(ex["key_concepts"])
        })
    
    with open(output_file, "w") as f:
        json.dump(serializable_extractions, f, indent=2)
    
    logger.info(f"Successfully saved document extractions to {output_file}")

def save_questions_with_topics(questions, output_file="questions_with_topics.json"):
    """Save the generated questions with their topic combinations"""
    logger.info(f"Saving questions to {output_file}")
    with open(output_file, "w") as f:
        json.dump(questions, f, indent=2)
    
    logger.info(f"Successfully saved questions with topic combinations to {output_file}")

# -- Main Execution --------------------------------------------------------

if __name__ == "__main__":
    logger.info("Starting data generation process")
    
    # Create output directory if it doesn't exist
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # adjust this path to where your .pdf docs live
    docs_dir = "docs/"
    
    logger.info("Loading documents...")
    docs, filenames = load_docs_from_dir(docs_dir)
    logger.info(f"Loaded {len(docs)} documents")
    
    if not docs:
        logger.error("No documents found. Please check the docs directory.")
        exit(1)
    
    # 1) Extract topics & KCs
    logger.info("Extracting topics and key concepts...")
    extractions = extract_concepts_from_docs(docs, filenames)
    
    # Save extractions to file
    save_extractions(extractions, os.path.join(output_dir, "document_extractions.json"))
    
    # Verify we have valid extractions
    valid_extractions = [ex for ex in extractions if ex["topics"] or ex["key_concepts"]]
    if not valid_extractions:
        logger.error("No valid topics or key concepts extracted. Check your data and API responses.")
        exit(1)
    
    # 2) Build graph
    logger.info("Building concept graph...")
    G, topic_nodes, kc_nodes = build_concept_graph(extractions)
    
    if not topic_nodes:
        logger.error("No topics found in the graph. Cannot proceed.")
        exit(1)
    
    # 3) Sample combinations
    logger.info("Sampling concept combinations...")
    combos = sample_concept_combinations(G, topic_nodes, kc_nodes, num_samples=10)  # Reduced for testing
    
    if not combos:
        logger.error("Failed to generate concept combinations.")
        exit(1)
    
    # Save topic combinations
    topic_combinations_file = os.path.join(output_dir, "topic_combinations.json")
    logger.info(f"Saving topic combinations to {topic_combinations_file}")
    with open(topic_combinations_file, "w") as f:
        json.dump(combos, f, indent=2)
    
    # 4) Generate questions
    logger.info("Generating questions for each combination...")
    q_outputs = generate_questions_for_samples(combos, docs, extractions)
    
    # Save questions with topics
    save_questions_with_topics(q_outputs, os.path.join(output_dir, "questions_with_topics.json"))
    
    # Display results
    logger.info("\n===== GENERATED QUESTIONS =====")
    for idx, out in enumerate(q_outputs, 1):
        logger.info(f"\nSample {idx}:")
        logger.info(f"Topics: {out['topics']}")
        logger.info(f"Key Concepts: {out['key_concepts']}")
        logger.info(f"Reference Files: {out['reference_files']}")
        logger.info("Questions:")
        for q in out['questions']:
            logger.info(f" - {q}")
    
    logger.info(f"\nAll outputs saved to directory: {output_dir}") 