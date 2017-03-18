import hetio.hetnet
import collections
import numpy
import pytest

   
    
def dual_normalize(matrix, row_damping=0, column_damping=0):
    """
    Row and column normalize a 2d numpy array
    """
    row_sums = matrix.sum(axis=1)
    column_sums = matrix.sum(axis=0)
    # Normalize rows, unless row_damping is 0
    if row_damping != 0:
        for j, row_sum in enumerate(row_sums):
            if row_sum == 0:
                continue
            matrix[j, :] *= row_sum ** -row_damping
    # Normalize columns, unless column_damping is 0
    if column_damping != 0:
        for i, column_sum in enumerate(column_sums):
            if column_sum == 0:
                continue
            matrix[:, i] *= column_sum ** -column_damping
    
    return matrix


def get_node_to_position(graph, metanode):
    """
    Given a metanode, return a dictionary of node to position
    """
    if not isinstance(metanode, hetio.hetnet.MetaNode):
        # metanode is a name
        metanode = graph.node_dict(metanode)
    metanode_to_nodes = graph.get_metanode_to_nodes()
    nodes = sorted(metanode_to_nodes[metanode])
    node_to_position = collections.OrderedDict((n, i) for i, n in enumerate(nodes))
    return node_to_position


def metaedge_to_adjacency_matrix(graph, metaedge):
    """
    Returns an adjacency matrix where source nodes are columns and target nodes are rows
    """
    if not isinstance(metaedge, hetio.hetnet.MetaEdge):
        # metaedge is an abbreviation
        metaedge = graph.metagraph.metapath_from_abbrev(metaedge)[0]
    source_nodes = list(get_node_to_position(graph, metaedge.source))
    target_node_to_position = get_node_to_position(graph, metaedge.target)
    adjacency_matrix = numpy.zeros((len(target_node_to_position), len(source_nodes)))
    for j, source_node in enumerate(source_nodes):
        for edge in source_node.edges[metaedge]:
            i = target_node_to_position[edge.target]
            adjacency_matrix[i, j] = 1
    return adjacency_matrix


def diffuse_along_metapath(graph, metapath, source_node_weights, column_damping=1, row_damping=0):
    """
    Parameters
    ==========
    graph : hetio.hetnet.Graph
        graph to extract adjacency matrixes along
    metapath : hetio.hetnet.MetaPath
        metapath to diffuse along
    source_node_weights : dict
        dictionary of node to weight. Nodes not in dict are zero-weighted
    column_damping : scalar
        exponent of (out)degree in column normalization
    row_damping : scalar
        exponent of (in)degree in row normalization
    """
    
    # Initialize node weights
    source_metanode = metapath.source()
    source_node_to_position = get_node_to_position(graph, source_metanode)
    node_scores = numpy.zeros(len(source_node_to_position))
    for source_node, weight in source_node_weights.items():
        i = source_node_to_position[source_node]
        node_scores[i] = weight
    
    for metaedge in metapath:
        adjacency_matrix = metaedge_to_adjacency_matrix(graph, metaedge)

        # Row/column normalization with degree damping
        adjacency_matrix = dual_normalize(adjacency_matrix, row_damping, column_damping)

        # Can use @ in Python 3.5+ https://www.python.org/dev/peps/pep-0465/
        node_scores = adjacency_matrix.dot(node_scores)


    target_metanode = metapath.target()
    target_node_to_position = get_node_to_position(graph, target_metanode)
    node_to_score = collections.OrderedDict(zip(target_node_to_position, node_scores))
    return node_to_score



def test_dual_normalize():
'''
    First attempt at a pytest test.
    The test itself runs properly, and checks
    that dual_normalize is doing what it is supposed to.
'''
    toy_matrix = numpy.array([ 
        [1, 1, 1],
        [1, 1, 0],
        [1, 0, 0]
        ])
    toy_matrix = toy_matrix.astype('float64')
    toy_copy = toy_matrix.copy()
    test1 = dual_normalize( toy_copy, 0.0, 0.0 )
    test1 = test1.astype('float64')
    assert(  numpy.sum(numpy.absolute(toy_matrix-test1)) == 0 )

    test_exponent = 0.5
    toy_copy = toy_matrix.copy()
    test2 = dual_normalize( toy_copy, test_exponent, 0.0 )
    test2.astype('float64')
    true_matrix2 = numpy.array([ 
        [1/3**test_exponent, 1/3**test_exponent, 1/3**test_exponent],
        [1/2**test_exponent, 1/2**test_exponent, 0],
        [1, 0, 0]
        ])
    assert(  numpy.sum(numpy.absolute(true_matrix2-test2)) < 10*numpy.finfo(float).eps )

    test_exponent = 0.3
    toy_copy = toy_matrix.copy()
    test3 = dual_normalize( toy_copy, 0, test_exponent )
    true_matrix3 = numpy.array([ 
        [1/3**test_exponent, 1/3**test_exponent, 1/3**test_exponent],
        [1/2**test_exponent, 1/2**test_exponent, 0],
        [1, 0, 0]
        ])
    true_matrix3 = numpy.transpose(true_matrix3)
    assert(  numpy.sum(numpy.absolute(true_matrix3-test3)) < 10*numpy.finfo(float).eps )