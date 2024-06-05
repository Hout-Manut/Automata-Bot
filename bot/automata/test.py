
import graphviz

# Data
states = ['q0', 'q1', 'q2']
alphabet = ['a', 'b']
transitions = {
    ('q0', 'a'): 'q1',
    ('q0', 'b'): 'q2',
    ('q1', 'a'): 'q2',
    ('q1', 'b'): 'q0',
    ('q2', 'a'): 'q0',
    ('q2', 'b'): 'q1'
}
initial_state = 'q0'
final_states = ['q2']

# Initialize the graph with fixed square dimensions
fa_graph = graphviz.Digraph(format='png', graph_attr={
                            'size': '10,10', 'ratio': '1', 'dpi': '200'})

# Add states
for state in states:
    if state in final_states:
        fa_graph.node(state, shape='doublecircle')
    else:
        fa_graph.node(state)

# Add initial state marker
fa_graph.node('', shape='point')  # Invisible starting point
fa_graph.edge('', initial_state)

# Add transitions
for (start, symbol), end in transitions.items():
    fa_graph.edge(start, end, label=symbol)

# Save and render the graph
fa_graph.render('storage/graph_cache/finite_automaton_diagram')
