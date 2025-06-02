def extract_kp_combinations(G: nx.Graph) -> list[tuple[str,...]]:
    """
    Extract knowledge point combinations from the graph.
    Returns list of tuples containing connected knowledge points.
    """
    logger.info("Extracting knowledge point combinations from graph...")
    
    # Check if graph is empty
    if not G.nodes():
        logger.error("Graph is empty - no nodes found")
        return []
        
    combos = []
    try:
        # one-hop: direct edges
        combos += [(u, v) for u, v in G.edges()]
        logger.info(f"Found {len(combos)} one-hop combinations")
        
        # two-hop: nodes at distance exactly 2
        two_hop = []
        for u, v in combinations(G.nodes(), 2):
            if nx.has_path(G, u, v) and nx.shortest_path_length(G, u, v) == 2:
                two_hop.append((u, v))
        combos.extend(two_hop)
        logger.info(f"Found {len(two_hop)} two-hop combinations")
        
        # three-hop: core KPI
        try:
            core = max(G.degree, key=lambda x: x[1])[0]
            three_hop = []
            for node in G.nodes():
                if node != core and nx.has_path(G, core, node) and nx.shortest_path_length(G, core, node) == 3:
                    three_hop.append((core, node))
            combos.extend(three_hop)
            logger.info(f"Found {len(three_hop)} three-hop combinations")
        except ValueError as e:
            logger.error(f"Error finding core node: {e}")
        
        # community: cliques of size 3
        cliques = []
        for clique in nx.find_cliques(G):
            if len(clique) == 3:
                cliques.append(tuple(clique))
        combos.extend(cliques)
        logger.info(f"Found {len(cliques)} clique combinations")
        
        # Remove duplicates while preserving order
        unique_combos = list(dict.fromkeys(combos))
        logger.info(f"Total unique combinations found: {len(unique_combos)}")
        return unique_combos
        
    except Exception as e:
        logger.error(f"Error extracting combinations: {e}")
        return [] 

def build_kp_graph(clustered_kps_list: list[list[str]]) -> nx.Graph:
    """
    Build a knowledge point relationship graph from clustered knowledge points.
    Returns a NetworkX graph where nodes are knowledge points and edges represent co-occurrence.
    """
    logger.info("Building knowledge point relationship graph...")
    logger.info(f"Input clustered_kps_list: {clustered_kps_list}")
    
    G = nx.Graph()
    cooccur = {}
    
    # Log the structure of input data
    logger.info(f"Number of clusters: {len(clustered_kps_list)}")
    for i, cluster in enumerate(clustered_kps_list):
        logger.info(f"Cluster {i}: {cluster}")
    
    # Build co-occurrence dictionary
    for kps in clustered_kps_list:
        if not kps:  # Skip empty clusters
            logger.warning("Found empty cluster, skipping")
            continue
            
        logger.info(f"Processing cluster: {kps}")
        for a, b in combinations(kps, 2):
            pair = tuple(sorted((a, b)))
            cooccur[pair] = cooccur.get(pair, 0) + 1
            logger.info(f"Added co-occurrence for pair: {pair}")
    
    # Log co-occurrence statistics
    logger.info(f"Number of co-occurrence pairs: {len(cooccur)}")
    if cooccur:
        logger.info(f"Sample co-occurrence pairs: {list(cooccur.items())[:5]}")
    
    # Build graph
    for (a, b), w in cooccur.items():
        G.add_node(a)
        G.add_node(b)
        G.add_edge(a, b, weight=w)
        logger.info(f"Added edge: {a} -- {b} with weight {w}")
    
    # Log graph statistics
    logger.info(f"Final graph has {len(G.nodes())} nodes and {len(G.edges())} edges")
    if G.nodes():
        logger.info(f"Sample nodes: {list(G.nodes())[:5]}")
    if G.edges():
        logger.info(f"Sample edges: {list(G.edges())[:5]}")
    
    return G

def extract_knowledge_points(question: str, solution: str) -> list[str]:
    """
    Extract knowledge points from a question and its solution.
    Returns a list of knowledge points.
    """
    logger.info(f"Extracting knowledge points from question: {question[:100]}...")
    
    prompt = f"""As a physics education specialist, analyze the given physics problem and its solution to
extract specific physics knowledge points. Provide ≤10 concise, directly relevant points.

Physics Problem: {question}
Solution: {solution}

Output format:
Knowledge Points:
1.
2.
..."""
    try:
        resp = client.chat.completions.create(
            model="Qwen/Qwen3-235B-A22B-fp8-tput",
            messages=[{"role":"user","content":prompt}]
        )
        logger.info("LLM call completed successfully")
        
        output = resp.choices[0].message.content
        logger.info(f"Raw LLM output: {output}")
        
        lines = output.splitlines()
        kps = [l.split('.',1)[1].strip() for l in lines if l.strip().startswith(tuple(str(i) for i in range(1,11)))]
        
        logger.info(f"Extracted {len(kps)} knowledge points:")
        for i, kp in enumerate(kps, 1):
            logger.info(f"{i}. {kp}")
            
        return kps
    except Exception as e:
        logger.error(f"Error extracting knowledge points: {e}")
        return []

def cluster_knowledge_points(kps: list[str]) -> str:
    """
    Cluster a list of knowledge points and return a representative point.
    Returns a single knowledge point that best represents the cluster.
    """
    if not kps:
        logger.warning("No knowledge points to cluster")
        return ""
        
    logger.info(f"Clustering {len(kps)} knowledge points")
    bullets = "\n".join(f"- {kp}" for kp in kps)
    
    prompt = f"""Given these physics KPs, pick the one best representing the group:
{bullets}

Provide:
Best Knowledge Point: <your choice>
Reason: <brief>"""
    
    try:
        resp = client.chat.completions.create(
            model="Qwen/Qwen3-235B-A22B-fp8-tput",
            messages=[{"role":"user","content":prompt}]
        )
        logger.info("LLM call completed successfully")
        
        output = resp.choices[0].message.content
        logger.info(f"Raw LLM output: {output}")
        
        for line in output.splitlines():
            if line.startswith("Best Knowledge Point:"):
                rep = line.split(":",1)[1].strip()
                logger.info(f"Selected representative point: {rep}")
                return rep
                
        logger.warning("No representative point found in output")
        return kps[0]  # fallback to first point
        
    except Exception as e:
        logger.error(f"Error clustering knowledge points: {e}")
        return kps[0] if kps else ""  # fallback to first point or empty string

def main(output_graph="kp_graph.graphml", output_synth_csv="output_synth_csv.csv"):
    logger.info("Starting main process...")
    
    try:
        # Read input data
        logger.info("Reading input data from merged_output.json")
        with open('merged_output.json', 'r') as f:
            data = json.load(f)
        
        # Create DataFrame
        rows = [
            {"question": entry.get("question", ""), "Solution": entry.get("Solution", "")}
            for entry in data.values()
        ]
        df = pd.DataFrame(rows)
        df = df.head(10)
        logger.info(f"Loaded {len(df)} rows from input data")
        
        # Process each row to extract knowledge points
        clustered_kps_list = []
        for idx, row in df.iterrows():
            try:
                logger.info(f"Processing row {idx+1}/{len(df)}")
                kps = extract_knowledge_points(row.question, row.Solution)
                if not kps:
                    logger.warning(f"Row {idx}: no KPs extracted, skipping.")
                    continue
                    
                rep = cluster_knowledge_points(kps)
                if not rep:
                    logger.warning(f"Row {idx}: clustering returned empty, skipping.")
                    continue
                    
                clustered_kps_list.append([rep])
                logger.info(f"Row {idx}: successfully processed")
                
            except Exception as e:
                logger.error(f"Row {idx}: error processing question: {e}")
                continue
        
        if not clustered_kps_list:
            logger.error("No knowledge points were extracted from any rows")
            return
            
        # Build and save KPRG
        logger.info("Building knowledge point relationship graph...")
        G = build_kp_graph(clustered_kps_list)
        
        if not G.nodes():
            logger.error("Built graph is empty - no nodes were created")
            return
            
        logger.info(f"Built graph with {len(G.nodes())} nodes and {len(G.edges())} edges")
        nx.write_graphml(G, output_graph)
        logger.info(f"KPRG saved to {output_graph}")
        
        # Enumerate combinations
        logger.info("Extracting knowledge point combinations...")
        combos = extract_kp_combinations(G)
        
        if not combos:
            logger.error("No combinations were found in the graph")
            return
            
        logger.info(f"Found {len(combos)} KP combinations")
        
        # Generate questions for combinations
        synth_qa = []
        for i, combo in enumerate(combos[:10]):
            try:
                logger.info(f"Processing combination {i+1}/10")
                combo_list = list(combo)
                new_q = generate_new_problem(combo_list)
                
                if not new_q:
                    logger.warning(f"Combo {combo_list}: no question generated, skipping.")
                    continue
                    
                synth_qa.append({
                    "combination": combo_list,
                    "question": new_q,
                    "solution": "Stay tuned !! will appear soon"
                })
                logger.info(f"Successfully generated question for combination {i+1}")
                
            except Exception as e:
                logger.error(f"Error processing combination {combo_list}: {e}")
                continue
        
        if not synth_qa:
            logger.error("No questions were generated")
            return
            
        # Save results
        out_df = pd.DataFrame(synth_qa)
        out_df.to_csv(output_synth_csv, index=False)
        logger.info(f"Synthetic QA saved to {output_synth_csv}")
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        return 