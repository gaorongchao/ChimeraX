# vim: set expandtab ts=4 sw=4:

# === UCSF ChimeraX Copyright ===
# Copyright 2016 Regents of the University of California.
# All rights reserved.  This software provided pursuant to a
# license agreement containing restrictions on its disclosure,
# duplication and use.  For details see:
# http://www.rbvi.ucsf.edu/chimerax/docs/licensing.html
# This notice must be embedded in or attached to all copies,
# including partial copies, of the software or any revisions
# or derivations thereof.
# === UCSF ChimeraX Copyright ===

# ------------------------------------------------------------------------------
#
from chimerax.core.tools import ToolInstance
class Plot(ToolInstance):

    def __init__(self, session, bundle_info, *, title='Plot'):
        ToolInstance.__init__(self, session, bundle_info)

        from chimerax.core.ui.gui import MainToolWindow
        tw = MainToolWindow(self)
        self.tool_window = tw
        parent = tw.ui_area

        from matplotlib import figure
        self.figure = f = figure.Figure(dpi=100, figsize=(2,2))

        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
        self.canvas = c = Canvas(f)
        c.setParent(parent)

        from PyQt5.QtWidgets import QHBoxLayout
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(c)
        parent.setLayout(layout)
        tw.manage(placement="right")

        self.axes = axes = f.gca()

    def show(self):
        self.tool_window.shown = True

    def hide(self):
        self.tool_window.shown = False

# ------------------------------------------------------------------------------
#
class ContactPlot(Plot):
    
    def __init__(self, session, groups, contacts, spring_constant):

        # Create matplotlib panel
        bundle_info = session.toolshed.find_bundle('contacts')
        Plot.__init__(self, session, bundle_info)

        self.groups = groups
        self.contacts = contacts
        
        # Create graph
        self.graph = self._make_graph(contacts)

        # Layout and plot graph
        self.undisplayed_color = (.8,.8,.8,1)	# Node color for undisplayed chains
        self._draw_graph(spring_constant)

        self.canvas.mousePressEvent = self._mouse_press

        self._handler = session.triggers.add_handler('atomic changes', self._atom_display_change)

        self.tool_window.ui_area.contextMenuEvent = self._show_context_menu
        
    def delete(self):
        self._session().triggers.remove_handler(self._handler)
        self._handler = None
        Plot.delete(self)

    def _make_graph(self, contacts):
        max_area = float(max(c.buried_area for c in contacts))
        import networkx as nx
        # Keep graph nodes in order so we can reproduce the same layout.
        from collections import OrderedDict
        class OrderedGraph(nx.Graph):
            node_dict_factory = OrderedDict
            adjlist_dict_factory = OrderedDict
        G = nx.OrderedGraph()
#        G = nx.Graph()
        for c in contacts:
            G.add_edge(c.group1, c.group2, weight = c.buried_area/max_area)
        return G

    def _draw_graph(self, spring_constant):
                
        G = self.graph
        axes = self.axes

        # Layout nodes
        kw = {} if spring_constant is None else {'k':spring_constant}
        from numpy.random import seed
        seed(1)	# Initialize random number generator so layout the same for the same input.
        import networkx as nx
        pos = nx.spring_layout(G, **kw) # positions for all nodes

        # Draw nodes
        # Sizes are areas define by matplotlib.pyplot.scatter() s parameter documented as point^2.
        node_sizes = tuple(0.05 * n.area for n in G)
        node_colors = tuple((n.color if n.shown() else self.undisplayed_color) for n in G)
        na = nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, ax=axes)
        na.set_picker(True)	# Generate mouse pick events for clicks on nodes
        self._node_artist = na
    
        # Draw edges
        self._edges = edges = []
        widths = []
        styles = []
        for (u,v,d) in G.edges(data=True):
            edges.append((u,v))
            large_area = d['weight'] >0.1
            widths.append(3 if large_area else 2)
            styles.append('solid' if large_area else 'dotted')
        ea = nx.draw_networkx_edges(G, pos, edgelist=edges, width=widths, style=styles, ax=axes)
        ea.set_picker(True)
        self._edge_artist = ea

        # Draw node labels
        short_names = {n:n.short_name for n in G}
        nx.draw_networkx_labels(G, pos, labels=short_names, font_size=16, font_family='sans-serif', ax=axes)

        # Hide axes and reduce border padding
        axes.get_xaxis().set_visible(False)
        axes.get_yaxis().set_visible(False)
        axes.axis('tight')
        self.figure.tight_layout(pad = 0, w_pad = 0, h_pad = 0)
        self.show()

    def _mouse_press(self, event):
        from PyQt5.QtCore import Qt
        if event.button() != Qt.LeftButton:
            return	# Only handle left button.  Right button will post menu.
        nodes = self._clicked_nodes(event.x(), event.y())
        shift_key = event.modifiers() & Qt.ShiftModifier

        if shift_key:
            self._select_nodes(nodes)
        else:
            n = len(nodes)
            if n == 0:
                self._show_all_atoms()
            elif n == 1:
                self._show_neighbors(nodes[0])
            else:
                # Edge clicked, pair of nodes
                self._show_node_atoms(nodes)
                    
    def _select_nodes(self, nodes):
        self._clear_selection()
        for g in nodes:
            g.atoms.selected = True

    def _clear_selection(self):
        self._session().selection.clear()

    def _show_node_atoms(self, nodes):
        gset = set(nodes)
        for h in self.groups:
            h.atoms.displays = (h in gset)

    def _show_neighbors(self, g):
        from .cmd import neighbors
        ng = neighbors(g, self.contacts)
        ng.add(g)
        for h in self.groups:
            h.atoms.displays = (h in ng)

    def _show_all_atoms(self):
        for g in self.groups:
            g.atoms.displays = True

    def _clicked_nodes(self, x, y):
        # Convert Qt click position to matplotlib MouseEvent
        h = self.tool_window.ui_area.height()
        from matplotlib.backend_bases import MouseEvent
        e = MouseEvent('context menu', self.canvas, x, h-y)

        # Check for node click
        c,d = self._node_artist.contains(e)
        if c:
            i = d['ind'][0]
            n = [self.graph.nodes()[i]]
        else:
            # Check for edge click
            ec,ed = self._edge_artist.contains(e)
            if ec:
                i = ed['ind'][0]
                n = self._edges[i]	# Two nodes connected by this edge
            else:
                # Background clicked
                n = []
        return n

    def _atom_display_change(self, name, changes):
        if 'display changed' in changes.atom_reasons():
            # Atoms shown or hidden.  Color hidden nodes gray.
            node_colors = tuple((n.color if n.shown() else self.undisplayed_color) for n in self.graph)
            self._node_artist.set_facecolor(node_colors)
            self.canvas.draw()	# Need to ask canvas to redraw the new colors.

    def _show_context_menu(self, event):
        widget = self.tool_window.ui_area
        h = widget.height()
        x, y = event.x(), h-event.y()
        from matplotlib.backend_bases import MouseEvent
        e = MouseEvent('context menu', self.canvas, x, y)
        nodes = self._clicked_nodes(event.x(), event.y())
        
        from PyQt5.QtWidgets import QMenu, QAction
        menu = QMenu(widget)

        if nodes:
            node_names = ','.join(n.name for n in nodes)
            sel = QAction('Select %s' % node_names, widget)
            #sel.setStatusTip("Select specified chain")
            sel.triggered.connect(lambda checked, self=self, nodes=nodes: self._select_nodes(nodes))
            menu.addAction(sel)

            show = QAction('Show only %s' % node_names, widget)
            show.triggered.connect(lambda checked, self=self, nodes=nodes: self._show_node_atoms(nodes))
            menu.addAction(show)

            if len(nodes) == 1:
                sn = QAction('Show %s and neighbors' % node_names, widget)
                sn.triggered.connect(lambda checked, self=self, nodes=nodes: self._show_neighbors(nodes[0]))
                menu.addAction(sn)
                
        csel = QAction('Clear selection', widget)
        csel.triggered.connect(lambda checked, self=self: self._clear_selection())
        menu.addAction(csel)
        
        sat = QAction('Show all atoms', widget)
        sat.triggered.connect(lambda checked, self=self: self._show_all_atoms())
        menu.addAction(sat)
        
        menu.exec(event.globalPos())
