from flask import Flask, request, jsonify

app = Flask(__name__)

# Product-to-center mappings and weights
PRODUCT_INFO = {
    'A': {'center': 'C1', 'weight': 3},
    'B': {'center': 'C1', 'weight': 2},
    'C': {'center': 'C1', 'weight': 8},
    'D': {'center': 'C2', 'weight': 12},
    'E': {'center': 'C2', 'weight': 25},
    'F': {'center': 'C2', 'weight': 15},
    'G': {'center': 'C3', 'weight': 0.5},
    'H': {'center': 'C3', 'weight': 1},
    'I': {'center': 'C3', 'weight': 2},
}

# Complete distance matrix (bidirectional)
DISTANCES = {
    ('C1', 'L1'): 3, ('L1', 'C1'): 3,
    ('C2', 'L1'): 2.5, ('L1', 'C2'): 2.5,
    ('C3', 'L1'): 2, ('L1', 'C3'): 2,
    ('C1', 'C2'): 4, ('C2', 'C1'): 4,
    ('C1', 'C3'): 5, ('C3', 'C1'): 5,
    ('C2', 'C3'): 3, ('C3', 'C2'): 3,
}

def calculate_cost(weight, distance):
    """Calculate transportation cost with proper error handling"""
    if distance is None:
        return 0  # or raise an exception if preferred
    if weight <= 5:
        return 10 * distance
    additional = ((weight - 5) // 5) + 1
    return (10 + 8 * additional) * distance

def get_center_quantities(order):
    """Group products by centers with total weights"""
    centers = {'C1': 0, 'C2': 0, 'C3': 0}
    for product, qty in order.items():
        if product in PRODUCT_INFO and qty > 0:
            centers[PRODUCT_INFO[product]['center']] += PRODUCT_INFO[product]['weight'] * qty
    return {k: v for k, v in centers.items() if v > 0}

def evaluate_starting_center(start_center, center_weights):
    """Calculate total cost for a starting center"""
    total_cost = 0
    remaining_centers = [c for c in ['C1', 'C2', 'C3'] 
                        if c != start_center and center_weights.get(c, 0) > 0]
    
    # Deliver starting center's items
    if center_weights.get(start_center, 0) > 0:
        distance = DISTANCES.get((start_center, 'L1'), 0)
        total_cost += calculate_cost(center_weights[start_center], distance)
    
    # Fetch from other centers
    for next_center in remaining_centers:
        # Find route from current location (L1 after first delivery) to next center
        empty_distance = DISTANCES.get(('L1', next_center), 0)
        total_cost += calculate_cost(0, empty_distance)
        
        # Deliver from next center
        delivery_distance = DISTANCES.get((next_center, 'L1'), 0)
        total_cost += calculate_cost(center_weights[next_center], delivery_distance)
    
    return total_cost

@app.route('/calculate-cost', methods=['POST'])
def calculate_min_cost():
    try:
        order = request.get_json()
        if not order:
            return jsonify({"error": "No order data provided"}), 400
            
        center_weights = get_center_quantities(order)
        if not center_weights:
            return jsonify({"cost": 0})
        
        min_cost = min(
            evaluate_starting_center(candidate_center, center_weights)
            for candidate_center in ['C1', 'C2', 'C3']
            if candidate_center in center_weights or any(c in center_weights for c in ['C1', 'C2', 'C3'])
        )
        
        return jsonify({"cost": min_cost})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/')
def health_check():
    return jsonify({"status": "API is running"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)