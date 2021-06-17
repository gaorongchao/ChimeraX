# vim: set expandtab shiftwidth=4 softtabstop=4:

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

from chimerax.core.tools import ToolInstance
from chimerax.core.errors import UserError

from Qt.QtCore import Qt

class RenderByAttrTool(ToolInstance):

    #help = "help:user/tools/matchmaker.html"

    def __init__(self, session, tool_name):
        ToolInstance.__init__(self, session, tool_name)
        from chimerax.ui import MainToolWindow
        self.tool_window = tw = MainToolWindow(self, statusbar=True)
        parent = tw.ui_area
        from Qt.QtWidgets import QVBoxLayout, QHBoxLayout, QDialogButtonBox, QPushButton, QMenu, QLabel
        from Qt.QtWidgets import QTabWidget, QWidget
        from Qt.QtCore import Qt
        overall_layout = QVBoxLayout()
        overall_layout.setContentsMargins(0,0,0,0)
        overall_layout.setSpacing(0)
        parent.setLayout(overall_layout)

        target_layout = QHBoxLayout()
        overall_layout.addLayout(target_layout)

        target_layout.addWidget(QLabel("Attributes of"), alignment=Qt.AlignRight)
        self.target_menu_button = QPushButton()
        menu = QMenu()
        menu.triggered.connect(self._new_target)
        self.target_menu_button.setMenu(menu)
        target_layout.addWidget(self.target_menu_button, alignment=Qt.AlignLeft)
        model_list_layout = QVBoxLayout()
        target_layout.addLayout(model_list_layout)
        model_list_layout.addWidget(QLabel("Models"), alignment=Qt.AlignBottom)
        from chimerax.ui.widgets import ModelListWidget, MarkedHistogram
        class ShortModelListWidget(ModelListWidget):
            def sizeHint(self):
                sh = super().sizeHint()
                sh.setHeight(sh.height() // 2)
                return sh
        self.model_list = ShortModelListWidget(session, filter_func=self._filter_model)
        model_list_layout.addWidget(self.model_list, alignment=Qt.AlignTop)

        self.mode_widget = QTabWidget()
        overall_layout.addWidget(self.mode_widget)

        render_tab = QWidget()
        render_tab_layout = QVBoxLayout()
        render_tab.setLayout(render_tab_layout)
        attr_menu_layout = QHBoxLayout()
        render_tab_layout.addLayout(attr_menu_layout)
        attr_menu_layout.addWidget(QLabel("Attribute:"), alignment=Qt.AlignRight)
        self.attr_menu_button = QPushButton()
        menu = QMenu()
        menu.triggered.connect(self._new_render_attr)
        self.attr_menu_button.setMenu(menu)
        attr_menu_layout.addWidget(self.attr_menu_button, alignment=Qt.AlignLeft)
        self.render_histogram = MarkedHistogram(min_label=True, max_label=True, status_line=tw.status)
        render_tab_layout.addWidget(self.render_histogram)
        self.mode_widget.addTab(render_tab, "Render")

        sel_tab = QWidget()
        sel_layout = QVBoxLayout()
        sel_tab.setLayout(sel_layout)
        sel_layout.addWidget(QLabel("This tab not yet implemented.\nUse 'select' command instead.",
            alignment=Qt.AlignCenter))
        self.mode_widget.addTab(sel_tab, "Select")

        self._update_target_menu()

        from Qt.QtWidgets import QDialogButtonBox as qbbox
        bbox = qbbox(qbbox.Ok | qbbox.Apply | qbbox.Close | qbbox.Help)
        bbox.accepted.connect(self.render)
        bbox.button(qbbox.Apply).clicked.connect(self.render)
        bbox.accepted.connect(self.delete) # slots executed in the order they are connected
        bbox.rejected.connect(self.delete)
        #from chimerax.core.commands import run
        #bbox.helpRequested.connect(lambda *, run=run, ses=session: run(ses, "help " + self.help))
        bbox.button(qbbox.Help).setEnabled(False)
        overall_layout.addWidget(bbox)

        tw.manage(placement=None)

    def render(self):
        pass

    def _filter_model(self, model):
        try:
            return self._ui_to_info[self.target_menu_button.text()].model_filter(model)
        except (AttributeError, KeyError):
            return False

    def _new_render_attr(self, attr_info=None):
        if attr_info is None:
            attr_name = "choose attr"
        else:
            if isinstance(attr_info, str):
                attr_name = attr_info
            else:
                attr_name = attr_info.text()
        if attr_name != self.attr_menu_button.text():
            self.attr_menu_button.setText(attr_name)
            if attr_info is None:
                self.render_histogram.data_source = "Choose attribute to show histogram"
                #TODO: clear attr widgets
            else:
                #TODO: update attr widgets
                pass


    def _new_classes(self):
        self._update_target_menu()

    def _new_target(self, target):
        if not isinstance(target, str):
            target = target.text()
        self.target_menu_button.setText(target)
        self.model_list.refresh()
        self._update_render_attr_menu()

    def _update_render_attr_menu(self, call_new_attr=True):
        menu = self.attr_menu_button.menu()
        menu.clear()
        target = self.target_menu_button.text()
        attr_info = self._ui_to_info[target]
        from chimerax.core.attributes import MANAGER_NAME
        attr_mgr = self.session.get_state_manager(MANAGER_NAME)
        attr_names = attr_mgr.attributes_returning(attr_info.class_object, (int, float), none_okay=True)
        attr_names.sort()
        for attr_name in attr_names:
            menu.addAction(attr_name)
        if call_new_attr:
            self._new_render_attr()

    def _update_target_menu(self):
        from .manager import get_manager
        mgr = get_manager(self.session)
        self._ui_to_info = {}
        ui_names = []
        for pn in mgr.provider_names:
            ui_name = mgr.ui_name(pn)
            ui_names.append(ui_name)
            self._ui_to_info[ui_name] = mgr.render_attr_info(pn)
        ui_names.sort()
        menu = self.target_menu_button.menu()
        menu.clear()
        for ui_name in ui_names:
            menu.addAction(ui_name)
        if not self.target_menu_button.text() and ui_names:
            self._new_target(ui_names[0])

