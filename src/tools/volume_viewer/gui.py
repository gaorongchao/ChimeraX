# vim: set expandtab ts=4 sw=4:

# -----------------------------------------------------------------------------
# Graphical user interface to display surfaces, meshes, and images
# for 3 dimensional grid data.
#

from chimerax.core.tools import ToolInstance

# ------------------------------------------------------------------------------
#
class VolumeViewer(ToolInstance):

    SESSION_SKIP = True

    def __init__(self, session, bundle_info):
        ToolInstance.__init__(self, session, bundle_info)

        self.display_name = 'Volume Viewer'
        self.active_volume = None
        self.redisplay_in_progress = False

        from chimerax.core.ui.gui import MainToolWindow
        self.tool_window = tw = MainToolWindow(self)
        parent = tw.ui_area

        self.make_panels(parent)

        from PyQt5.QtWidgets import QVBoxLayout
        self.panel_layout = pl = QVBoxLayout(parent)
        pl.setContentsMargins(0,0,0,0)
        pl.setSpacing(0)

        from . import defaultsettings
        default_settings = defaultsettings.VolumeViewerDefaultSettings()
        default_settings.set_gui_to_defaults(self)
#        default_settings.add_change_callback(self.default_settings_changed_cb)

        tw.manage(placement="right")
    
        # Add any data sets opened prior to volume dialog being created.
        self.volume_opened_cb(volume_list(session))

        add_volume_opened_callback(session, self.volume_opened_cb)
        self.model_close_handler = add_volume_closed_callback(session, self.volume_closed_cb)
        
    def show(self):
        self.tool_window.shown = True

    def hide(self):
        self.tool_window.shown = False

    def show_panels(self, pnames):

        layout = self.panel_layout

        # Replace vertical panel layout
        while layout.count() > 0:
            layout.removeItem(layout.takeAt(0))
            
        for p in self.gui_panels:
            if p.name in pnames:
                layout.addWidget(p.frame)
    
    # ---------------------------------------------------------------------------
    #
    def message(self, text, append = False):

        return

        if append:
          self.message_label['text'] = self.message_label['text'] + text
        else:
          self.message_label['text'] = text

        from time import time
        if time() > self.message_time + self.message_minimum_time:
          # Calling update_idletasks() on every message causes hang when Morph Map
          # play used, Mac Chimera 1.5 pre-release, Oct 21, 2010.
          # Apparently no events get processed.
          self.message_label.update_idletasks()
          self.message_time = time()

    def set_step_cb(self, step):
        s = step
        self.volume.new_region(ijk_step = (s,s,s), adjust_step = False)
        self.step.setText('%d' % s)

    def set_level_cb(self):
        level = float(self.level.text())
        v = self.volume
        v.set_parameters(surface_levels = [level])
        v.show()

    def models_closed_cb(self, name, models):
        if self.volume in models:
            self.delete()

    # Override ToolInstance method
    def delete(self):
        s = self.session
        s.triggers.delete_handler(self.model_close_handler)
        from chimerax.core.map import Volume
        for v in s.models.list(type = Volume):
            v.remove_volume_change_callback(self.data_region_changed)
        super().delete()
      
    def make_panels(self, parent):
        # Order of panel_classes determines top to bottom location in dialog.
        # panel_classes = (Hybrid.Feature_Buttons_Panel,
        #                  Data_List_Panel,
        #                  Precomputed_Subsamples_Panel, Coordinates_Panel,
        #                  Thresholds_Panel, Brightness_Transparency_Panel,
        #                  Display_Style_Panel, Plane_Panel, Orthoplane_Panel,
        #                  Region_Size_Panel, Subregion_Panel,
        #                  Zone_Panel, Atom_Box_Panel, Named_Region_Panel,
        #                  Display_Options_Panel, Solid_Options_Panel,
        #                  Surface_Options_Panel)

        panel_classes = [Thresholds_Panel, Display_Style_Panel]

        self.gui_panels = panels = [pc(self, parent) for pc in panel_classes]
        #p.frame.grid(row = row, column = 0, sticky = 'news')
        #p.frame.grid_remove()
        for row, p in enumerate(panels):
            p.panel_row = row
            setattr(self, p.__class__.__name__.lower(), p)

#    sorted_panels = list(self.gui_panels)
#    sorted_panels.sort(lambda p1, p2: cmp(p1.name, p2.name))
#    self.feature_buttons_panel.set_panels(sorted_panels)
    
    # Make data panel expand vertically when dialog resized
#    data_list_panel_row = self.data_list_panel.panel_row
#    parent.rowconfigure(data_list_panel_row, weight = 1)

    # ---------------------------------------------------------------------------
    # Show data set parameters in dialog but do not render data.
    #
    def volume_opened_cb(self, vlist):

        for v in vlist:

            # Set data region status messages to display in volume dialog
            #v.message_cb = self.message

            # Update data list and menu.
            #line = v.name_with_id()
            #self.data_list_panel.list_region(line)

            #
            # Have to use id of volume object to avoid a memory leak.
            # In Aqua Chimera 1.2540 deleting data menu entry does not free command
            # leaving a reference to the volume if it is used as an argument.
            #
            #cb = lambda i=id(v): self.data_menu_cb(i)
            #self.data_menu.add_command(label = line, command = cb)
            #self.menu_volumes.append(v)

            # Add data values changed callback.
            v.add_volume_change_callback(self.data_region_changed)

            if hasattr(v.data, 'series_index') and v.data.series_index > 0:
                return

            # Show data parameters.
            self.display_volume_info(v)

            # Show plane panel if needed
            #from volume import show_one_plane, default_settings as ds
            #if show_one_plane(v.data.size, ds['show_plane'], ds['voxel_limit_for_plane']):
            #    self.plane_panel.panel_shown_variable.set(True)

    # ---------------------------------------------------------------------------
    #
    def volume_closed_cb(self, vlist):

    # Remove data menu and data listbox entries.
    # mv = self.menu_volumes
    # indices = [mv.index(v) for v in vlist]
    # indices.sort()
    # indices.reverse()
    # dm = self.data_menu
    # from CGLtk.Hybrid import base_menu_index
    # i0 = base_menu_index(dm)
    # for i in indices:
    #     self.data_list_panel.remove_listed_region(i)
    #     dm.delete(i+i0)
    #     del mv[i]

        # Remove data changed callbacks
        for v in vlist:
            v.remove_volume_change_callback(self.data_region_changed)

        # Update focus region.
        if self.active_volume in vlist:
            self.active_volume = None
            vset = set(vlist)
            vopen = [v for v in volume_list(self.session) if v.data and not v in vset]
            v = vopen[0] if len(vopen) > 0 else None
            self.display_volume_info(v)

    # ---------------------------------------------------------------------------
    #
    def display_volume_info(self, volume):

        self.active_volume = volume

        for p in self.gui_panels:
            if hasattr(p, 'update_panel_widgets'):
                p.update_panel_widgets(volume)
  
    # ---------------------------------------------------------------------------
    #
    def data_region_changed(self, v, type):

        tp = self.thresholds_panel

        if type == 'data values changed':
          if tp.histogram_shown(v):
            tp.update_histograms(v)

        elif type == 'displayed':
          if not tp.histogram_shown(v):
            # Histogram, data range, and initial thresholds are only displayed
            #  after data is shown to avoid reading data file for undisplayed data.
            tp.update_panel_widgets(v, activate = False)

        elif type == 'representation changed':
          tp.update_panel_widgets(v, activate = False)
          if v is self.active_volume:
            dsp = self.display_style_panel
            dsp.update_panel_widgets(v)

        elif type == 'region changed':
          if tp.histogram_shown(v):
            tp.update_histograms(v)
          if v is self.active_volume:
              pass
            # self.update_region_in_panels(*v.region)
            # dop = self.display_options_panel
            # if dop.adjust_camera.get():
            #   self.focus_camera_on_region(v)
          else:
            tp.update_panel_widgets(v, activate = False)

        elif type == 'thresholds changed':
          tp.update_panel_widgets(v, activate = False)

        elif type == 'colors changed':
          tp.update_panel_widgets(v, activate = False)
          # if v is self.active_volume:
          #   btp = self.brightness_transparency_panel
          #   btp.update_panel_widgets(v)

        # elif type == 'voxel limit changed':
        #   dop = self.display_options_panel
        #   dop.set_gui_voxel_limit(v.rendering_options)

        # elif type == 'coordinates changed':
        #   if v is self.active_volume:
        #     cp = self.coordinates_panel
        #     cp.update_panel_widgets(v)

        # elif type == 'rendering options changed':
        #   if v is self.active_volume:
        #     for p in (self.display_options_panel, self.surface_options_panel,
        #               self.solid_options_panel, self.orthoplane_panel):
        #       p.update_panel_widgets(v)
      
    # ---------------------------------------------------------------------------
    # Notify all panels that representation changed so they can update gui if
    # it depends on the representation.
    #
    def representation_changed(self, representation):

      for p in self.gui_panels:
        if hasattr(p, 'representation_changed'):
          p.representation_changed(representation)

    # ---------------------------------------------------------------------------
    # Update display if immediate redisplay mode is on.
    #
    def redisplay_needed_cb(self, event = None):

      if self.active_volume == None:
        return

      #
      # While in this routine another redisplay may be requested.
      # Remember so we can keep redisplaying until everything is up to date.
      #
      self.need_redisplay = True

      if self.redisplay_in_progress:
        # Don't try to redisplay if we are in the middle of redisplaying.
        return

#      dop = self.display_options_panel
#      while dop.immediate_update.get() and self.need_redisplay:
      while True and self.need_redisplay:
        self.need_redisplay = False
        self.redisplay_in_progress = True
        try:
          self.show_using_dialog_settings(self.active_volume)
        except:
          # Need this to avoid disabling automatic volume redisplay when
          # user cancels file read cancel or out of memory exception raised.
          self.redisplay_in_progress = False
          raise
        self.redisplay_in_progress = False
    
    # ---------------------------------------------------------------------------
    #
    def show_using_dialog_settings(self, data_region, recreate_thresholds = False):

      dr = data_region
      if dr == None:
        return

      # The voxel limit setting effects the region size panel computation of
      # step size.  So make sure that setting is applied before region size
      # panel settings are used.  Ick.
#      dop = self.display_options_panel
#      dop.use_gui_settings(dr)

      for p in self.gui_panels:
        if hasattr(p, 'use_gui_settings'):
          p.use_gui_settings(dr)

      dr.initialize_thresholds(first_time_only = not recreate_thresholds)
      dr.show()

def show_viewer_on_open(session):
    # Register callback to show volume viewer when a map is opened
    if not hasattr(session, '_registered_volume_viewer'):
        session._registered_volume_viewer = True
        from chimerax.core.models import ADD_MODELS
        session.triggers.add_handler(ADD_MODELS, lambda name, m, s=session: models_added_cb(m, s))
    

def models_added_cb(models, session):
    # Show volume viewer when a map is opened.
    from chimerax.core.map import Volume
    vlist = [m for m in models if isinstance(m, Volume)]
    if vlist:
        for v in vlist:
            bundle_info = session.toolshed.find_bundle('volume_viewer')
            vv = VolumeViewer(session, bundle_info, volume = v)
            vv.show()

# -----------------------------------------------------------------------------
# Chimera 1 volume dialog
#
class Volume_Dialog:
    
  buttons = ('Update', 'Center', 'Orient', 'Close',)
  
  def fillInUI(self, parent):

    self.gui_panels = []

    self.active_volume = None
    self.menu_volumes = []

    self.message_time = 0
    self.message_minimum_time = 0.5     # seconds between status messages

    tw = parent.winfo_toplevel()
    self.toplevel_widget = tw
    tw.withdraw()

    parent.columnconfigure(0, weight = 1)
    row = 1

    self.make_menus(parent)

    #
    # Specify a label width so dialog is not resized for long messages.
    #
    msg = Tkinter.Label(parent, width = 40, anchor = 'w', justify = 'left')
    msg.grid(row = row, column = 0, sticky = 'ew')
    row += 1
    self.message_label = msg

    ub = self.buttonWidgets['Update']
    self.update_button = ub
    self.update_button_pack_settings = ub.pack_info()
    ub.pack_forget()

    volume.add_session_save_callback(self.save_session_cb)
      
  # ---------------------------------------------------------------------------
  #
  def make_menus(self, parent):
    menubar = Tkinter.Menu(parent, type = 'menubar', tearoff = False)
    tw.config(menu = menubar)

    file_menu_entries = (('Open map...', self.open_cb),
                         ('Save map as...', self.save_data_cb),
                         ('Duplicate', self.duplicate_cb),
                         ('Remove surface', self.remove_surface_cb),
                         ('Close map', self.close_data_cb),
                         )
    Hybrid.cascade_menu(menubar, 'File', file_menu_entries)

    fmenu = Hybrid.cascade_menu(menubar, 'Features')
    for p in sorted_panels:
      fmenu.add_checkbutton(label = p.name,
                            variable = p.panel_shown_variable.tk_variable)
    fmenu.add_separator()
    feature_menu_entries = (
      ('Show only default panels', self.show_default_panels_cb),
      ('Save default panels', self.save_default_panels_cb),
      ('Save default dialog settings', self.save_default_settings_cb),
      ('Use factory default settings', self.use_factory_defaults_cb))
    for name, cb in feature_menu_entries:
      fmenu.add_command(label = name, command = cb)

    self.data_menu = Hybrid.cascade_menu(menubar, 'Data')
    from chimera import triggers
    triggers.addHandler('Model', self.volume_name_change_cb, None)

    self.tools_menu = Hybrid.cascade_menu(menubar, 'Tools', ())
    self.update_tools_menu()

    from chimera.tkgui import aquaMenuBar
    aquaMenuBar(menubar, parent, row = 0)
      
  # ---------------------------------------------------------------------------
  #
  def find_gui_panel(self, name):

    for p in self.gui_panels:
      if p.name == name:
        return p
    return None

  # ---------------------------------------------------------------------------
  #
  def shown_panels(self):

    pshown = filter(lambda p: p.panel_shown_variable.get(), self.gui_panels)
    pshown.sort()
    return pshown

  # ---------------------------------------------------------------------------
  #
  def update_default_panels(self, pnames):

    # Don't show panel close buttons for default panels.
    for p in self.gui_panels:
      p.show_close_button = not (p.name in pnames)

  # ---------------------------------------------------------------------------
  #
  def show_default_panels_cb(self):

    from volume import default_settings
    self.show_panels(default_settings['shown_panels'])
    
  # ---------------------------------------------------------------------------
  #
  def default_settings_changed_cb(self, default_settings, changes):

    dop = self.display_options_panel
    dop.default_settings_changed(default_settings, changes)
    srp = self.subregion_panel
    srp.default_settings_changed(default_settings, changes)

  # ---------------------------------------------------------------------------
  #
  def save_default_settings_cb(self):

    from volume import default_settings as ds
    ds.set_defaults_from_gui(self, panel_settings = False)
    ds.save_to_preferences_file(panel_settings = False)
    
  # ---------------------------------------------------------------------------
  #
  def save_default_panels_cb(self):

    from volume import default_settings as ds
    ds.set_defaults_from_gui(self, data_settings = False,
                             global_settings = False)
    ds.save_to_preferences_file(data_settings = False, global_settings = False)
    self.update_default_panels(ds['shown_panels'])

  # ---------------------------------------------------------------------------
  #
  def use_factory_defaults_cb(self):

    from volume import default_settings
    default_settings.restore_factory_defaults(self)
    self.redisplay_needed_cb()

  # ---------------------------------------------------------------------------
  #
  def update_tools_menu(self):

    m = self.tools_menu
    m.delete(0, 'end')
    from chimera.extension import manager
    cat = manager.findCategory('Volume Data')
    tool_menu_entries = [(e.name(), lambda e=e, cat=cat: e.menuActivate(cat))
                         for e in cat.sortedEntries()
                         if e.name() != 'Volume Viewer']
    from CGLtk import Hybrid
    Hybrid.add_menu_entries(m, tool_menu_entries)
    
  # ---------------------------------------------------------------------------
  #
  def save_session_cb(self, file):

    import session
    session.save_volume_dialog_state(self, file)

  # ---------------------------------------------------------------------------
  #
  def open_cb(self):
      
    show_volume_file_browser('Open Volume Files', show_data = True)

  # ---------------------------------------------------------------------------
  #
  def volume_name_change_cb(self, trigger, x, changes):

    if 'name changed' in changes.reasons:
      from volume import Volume
      vlist = [m for m in changes.modified
               if isinstance(m, Volume) and m in self.menu_volumes]
      dm = self.data_menu
      from CGLtk.Hybrid import base_menu_index
      i0 = base_menu_index(dm)
      for v in vlist:
        dm.entryconfigure(self.menu_volumes.index(v)+i0, label = v.name)

  # ---------------------------------------------------------------------------
  #
  def data_menu_cb(self, vol_id):

    vol = [v for v in self.menu_volumes if id(v) == vol_id][0]
    self.display_volume_info(vol)
    self.redisplay_needed_cb()

  # ---------------------------------------------------------------------------
  #
  def selected_regions(self):

    rlist = self.data_list_panel.selected_list_regions()
    if len(rlist) == 0 and self.active_volume:
      rlist = [self.active_volume]
    return rlist
      
  # ---------------------------------------------------------------------------
  #
  def Update(self):

    self.show_cb()
      
  # ---------------------------------------------------------------------------
  #
  def show_cb(self, event = None):

    data_regions = self.selected_regions()
    for dr in data_regions:
      # For region displayed in dialog use the current dialog settings.
      if dr == self.active_volume:
        self.show_using_dialog_settings(dr, recreate_thresholds = True)
      else:
        # Set display style of data regions if needed.
        if dr.representation == None:
          dr.representation = self.display_style_panel.representation
          
        # Set initial thresholds if there are currently no thresholds.
        dr.initialize_thresholds(first_time_only = False)
        dr.show() # Display region not shown in dialog.

  # ---------------------------------------------------------------------------
  #
  def show_region(self, data_region, representation):

    self.display_volume_info(data_region)
    self.display_style_panel.representation = representation
    self.show_using_dialog_settings(data_region)

  # ---------------------------------------------------------------------------
  # Notify user interface panels of region bounds change.
  #
  def update_region_in_panels(self, ijk_min, ijk_max, ijk_step):
    
    for p in self.gui_panels:
      if hasattr(p, 'update_panel_ijk_bounds'):
        p.update_panel_ijk_bounds(ijk_min, ijk_max, ijk_step)
    
  # ---------------------------------------------------------------------------
  #
  def rendering_options_from_gui(self):

    from volume import Rendering_Options
    ro = Rendering_Options()
    dop = self.display_options_panel
    dop.rendering_options_from_gui(ro)
    slop = self.solid_options_panel
    slop.rendering_options_from_gui(ro)
    sop = self.surface_options_panel
    sop.rendering_options_from_gui(ro)
    return ro
    
  # ---------------------------------------------------------------------------
  # Update display even if immediate redisplay mode is off.
  # This is used when the pressing return in entry fields.
  #
  def redisplay_cb(self, event = None):

    #
    # TODO: probably want to avoid recursive shows just like in
    #  redisplay_needed_cb().  The purpose of avoiding recursive
    #  redisplay is to accumulate many (eg threshold) changes made
    #  when system is responding slowly, so each one does not require
    #  a separate redisplay.
    #
    if self.active_volume:
      self.show_using_dialog_settings(self.active_volume,
                                      recreate_thresholds = True)

  # ---------------------------------------------------------------------------
  #
  def Center(self):

    self.center_cb()

  # ---------------------------------------------------------------------------
  #
  def center_cb(self):

    if self.active_volume:
      self.focus_camera_on_region(self.active_volume)

  # ---------------------------------------------------------------------------
  #
  def focus_camera_on_region(self, data_region):

    xform = data_region.model_transform()
    if xform == None:
      return

    xyz_min, xyz_max = data_region.xyz_bounds()
    dx, dy, dz = map(lambda a,b: b-a, xyz_min, xyz_max)
    import math
    view_radius = .5 * math.sqrt(dx*dx + dy*dy + dz*dz)

    center = map(lambda a,b: .5*(a+b), xyz_min, xyz_max)
    center_point = apply(chimera.Point, center)
    center_eye = xform.apply(center_point)          # in eye coordinates
    v = chimera.viewer
    c = v.camera
    c.center = (center_eye.x, center_eye.y, center_eye.z)

    v.setViewSizeAndScaleFactor(view_radius, 1)
    v.clipping = False
      
  # ---------------------------------------------------------------------------
  #
  def Orient(self):

    self.orient_cb()

  # ---------------------------------------------------------------------------
  #
  def orient_cb(self):

    data_region = self.active_volume
    if data_region == None:
      return
    
    xform = data_region.model_transform()
    if xform == None:
      return

    xyz_min, xyz_max = data_region.xyz_bounds()
    cx, cy, cz = map(lambda a,b: .5*(a+b), xyz_min, xyz_max)
    c = chimera.Point(cx, cy, cz)
    ceye = xform.apply(c)
    xf1 = chimera.Xform.translation(-ceye.x, -ceye.y, -ceye.z)
    axis, angle = xform.getRotation()
    xf2 = chimera.Xform.rotation(axis, -angle)
    xf3 = chimera.Xform.translation(ceye.x, ceye.y, ceye.z)
    xf = chimera.Xform.identity()
    xf.multiply(xf3)
    xf.multiply(xf2)
    xf.multiply(xf1)

    ostates = {}
    for m in chimera.openModels.list(all = 1):
      ostates[m.openState] = 1

    active_ostates = filter(lambda ostate: ostate.active, ostates.keys())
    for ostate in active_ostates:
      ostate.globalXform(xf)
      
  # ---------------------------------------------------------------------------
  #
  def unshow_cb(self):

    for r in self.selected_regions():
      r.unshow()

  # ---------------------------------------------------------------------------
  #
  def save_data_cb(self):

    from VolumeData import select_save_path
    select_save_path(self.save_dialog_cb)

  # ---------------------------------------------------------------------------
  #
  def save_dialog_cb(self, path, file_type):

    dr = self.active_volume
    if dr == None:
      return

    try:
      dr.write_file(path, file_type)
    except ValueError as e:
      from chimera.replyobj import warning
      warning('File not saved. %s.' % e)

  # ---------------------------------------------------------------------------
  #
  def duplicate_cb(self):

    r = self.active_volume
    if r == None:
      return

    dr = r.copy()
    self.display_volume_info(dr)
    dr.show()
  
  # ---------------------------------------------------------------------------
  #
  def CloseData(self):

    self.close_data_cb()
      
  # ---------------------------------------------------------------------------
  #
  def close_data_cb(self):

    import volume
    volume.remove_volumes(self.selected_regions())
    
  # ---------------------------------------------------------------------------
  #
  def remove_surface_cb(self):

    for dr in self.selected_regions():
      dr.remove_surfaces()

# -----------------------------------------------------------------------------
#
class PopupPanel:

  def __init__(self, parent, resize_dialog = True):

    from PyQt5.QtWidgets import QFrame

    self.frame = QFrame(parent)

#        v = BooleanVariable(parent)
#        self.panel_shown_variable = v
#        v.add_callback(self.show_panel_cb)

    self.close_button = None
    self.show_close_button = True
    self.resize_dialog = resize_dialog
    
  # ---------------------------------------------------------------------------
  #
  def show_panel_cb(self):

    show = self.panel_shown_variable.get()
    if show:
      self.frame.grid()
      if self.close_button:
        if self.show_close_button:
          self.close_button.grid()
        else:
          self.close_button.grid_remove()
    else:
      self.frame.grid_remove()

    if self.resize_dialog:
      self.frame.winfo_toplevel().geometry('')    # Allow toplevel resize.
    
  # ---------------------------------------------------------------------------
  #
  def shown(self):

    return self.panel_shown_variable.get()

  # ---------------------------------------------------------------------------
  #
  def make_close_button(self, parent):

    b = Tkinter.Button(parent,
                       image = self.close_button_bitmap(),
                       command = self.close_panel_cb)
    self.close_button = b
    return b

  # ---------------------------------------------------------------------------
  #
  def close_panel_cb(self):

    self.panel_shown_variable.set(False)

  # ---------------------------------------------------------------------------
  # Used for closing panels.
  #
  def close_button_bitmap(self):

    return bitmap('x')

# -----------------------------------------------------------------------------
#
bitmap_specs = (
      ('x',
'''#define x_width 9
#define x_height 8
static unsigned char x_bits[] = {
   0x83, 0x01, 0xc6, 0x00, 0x6c, 0x00, 0x38, 0x00, 0x38, 0x00, 0x6c, 0x00,
   0xc6, 0x00, 0x83, 0x01};
'''),
      ('eye',
'''#define eye_width 16
#define eye_height 11
static unsigned char eye_bits[] = {
   0x00, 0x00, 0x00, 0x00, 0xe0, 0x07, 0x38, 0x1c, 0x88, 0x11, 0xcc, 0x33,
   0x88, 0x11, 0x38, 0x1c, 0xe0, 0x07, 0x00, 0x00, 0x00, 0x00};
'''),
      ('closed eye',
'''#define closed_eye_width 16
#define closed_eye_height 11
static unsigned char closed_eye_bits[] = {
   0x00, 0x00, 0x00, 0x00, 0xe0, 0x07, 0x38, 0x1c, 0x08, 0x10, 0x0c, 0x30,
   0x08, 0x10, 0x38, 0x1c, 0xe0, 0x07, 0x00, 0x00, 0x00, 0x00};
'''),
      ('dash',
'''#define dash_width 9
#define dash_height 8
static unsigned char dash_bits[] = {
   0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xfe, 0x00, 0xfe, 0x00, 0x00, 0x00,
   0x00, 0x00, 0x00, 0x00};
'''),
      )

# -----------------------------------------------------------------------------
# Create Tk bitmaps of standard icons.
#
bitmaps = {}
def bitmap(name):

  global bitmaps, bitmap_specs
  if not bitmaps:
    for n, bmap in bitmap_specs:
      bitmaps[n] = Tkinter.BitmapImage(data = bmap, foreground = 'black')

  return bitmaps.get(name, None)

# -----------------------------------------------------------------------------
# User interface for showing list of data sets.
#
class Data_List_Panel(PopupPanel):

  name = 'Data set list'           # Used in feature menu.
  
  def __init__(self, dialog, parent):

    self.dialog = dialog

    PopupPanel.__init__(self, parent)

    frame = self.frame
    frame.columnconfigure(0, weight = 1)

    row = 0

    hf = Tkinter.Frame(frame)
    hf.grid(row = row, column = 0, sticky = 'ew')
    hf.columnconfigure(1, weight = 1)
    row += 1
    
    h = Tkinter.Label(hf, text = 'Data Sets')
    h.grid(row = 0, column = 0, sticky = 'w')
    
    b = self.make_close_button(hf)
    b.grid(row = 0, column = 1, sticky = 'e')
    
    rl = Hybrid.Scrollable_List(frame, None, 3, self.region_selection_cb)
    self.region_listbox = rl.listbox
    rl.frame.grid(row = row, column = 0, sticky = 'news')
    frame.rowconfigure(row, weight = 1)
    row += 1

  # ---------------------------------------------------------------------------
  #
  def update_panel_widgets(self, data_region):

    pass

  # ---------------------------------------------------------------------------
  #
  def region_selection_cb(self, event):

    rlist = self.selected_list_regions()
    if len(rlist) == 1:
      self.dialog.display_volume_info(rlist[0])
      self.dialog.redisplay_needed_cb()

  # ---------------------------------------------------------------------------
  #
  def selected_list_regions(self):

    indices = map(int, self.region_listbox.curselection())
    mv = self.dialog.menu_volumes
    regions = [mv[i] for i in indices]
    return regions

  # ---------------------------------------------------------------------------
  #
  def list_region(self, line):

    self.region_listbox.insert('end', line)

  # ---------------------------------------------------------------------------
  #
  def remove_listed_region(self, index):

    self.region_listbox.delete(index)

  # ---------------------------------------------------------------------------
  #
  def use_gui_settings(self, data_region):

    pass

# -----------------------------------------------------------------------------
# User interface for opening precomputed subsamples.
#
class Precomputed_Subsamples_Panel(PopupPanel):

  name = 'Precomputed subsamples'           # Used in feature menu.
  
  def __init__(self, dialog, parent):

    self.dialog = dialog

    PopupPanel.__init__(self, parent)

    frame = self.frame
    frame.columnconfigure(2, weight = 1)
    
    pss = Hybrid.Option_Menu(frame, 'Precomputed subsamplings ')
    pss.frame.grid(row = 0, column = 0, sticky = 'w')
    pss.add_callback(self.subsample_menu_cb)
    self.subsampling_menu = pss

    oss = Tkinter.Button(frame, text = 'Open...',
                         command = self.open_subsamplings_cb)
    oss.grid(row = 0, column = 1, sticky = 'w')
    
    b = self.make_close_button(frame)
    b.grid(row = 0, column = 2, sticky = 'e')
    
  # ---------------------------------------------------------------------------
  #
  def update_panel_widgets(self, data_region):

    if data_region == None:
      self.subsampling_menu.remove_all_entries()
    else:
      self.update_subsample_menu(data_region)
    
  # ---------------------------------------------------------------------------
  #
  def open_subsamplings_cb(self):

    from VolumeData.opendialog import show_grid_file_browser
    show_grid_file_browser('Open Subsampled Volumes', self.open_subsamplings)

  # ---------------------------------------------------------------------------
  #
  def open_subsamplings(self, grid_objects):

    data_region = active_volume()
    if data_region == None:
      return
    data = data_region.data

    import subsample
    for g in grid_objects:
      cell_size = subsample.cell_size(g.size, g.name, data.size, data.name,
                                      self.dialog.toplevel_widget)
      if cell_size and cell_size != (1,1,1):
        self.open_subsamples(data_region.data, g, cell_size)

  # ---------------------------------------------------------------------------
  #
  def open_subsamples(self, data, grid_object, cell_size):
    
    from VolumeData import Subsampled_Grid
    if isinstance(data, Subsampled_Grid):
      ssdata = data
    else:
      ssdata = Subsampled_Grid(data)
      import volume
      volume.replace_data(data, ssdata)
    
    ssdata.add_subsamples(grid_object, cell_size)

    data_region = active_volume()
    if data_region.data == ssdata:
      self.update_subsample_menu(data_region)

  # ---------------------------------------------------------------------------
  #
  def update_subsample_menu(self, data_region):

    ssm = self.subsampling_menu
    ssm.remove_all_entries()
    if data_region:
      ssm.add_entry('full data')
      data = data_region.data
      if hasattr(data, 'available_subsamplings'):
        sslist = data.available_subsamplings.keys()
        sslist.sort()
        for subsampling in sslist:
          if tuple(subsampling) != (1,1,1):
            ssm.add_entry(step_text(subsampling))
      self.set_subsample_menu(data_region)
    
  # ---------------------------------------------------------------------------
  #
  def set_subsample_menu(self, data_region):

    ijk_min, ijk_max, ijk_step = data_region.region
    subsampling, ss_size = data_region.choose_subsampling(ijk_step)

    if tuple(subsampling) == (1,1,1):
      text = 'full data'
    else:
      text = step_text(subsampling)

    self.subsampling_menu.variable.set(text, invoke_callbacks = 0)
    
  # ---------------------------------------------------------------------------
  # Currently don't do anything when subsample menu selection is changed.
  #
  def subsample_menu_cb(self):

    text = self.subsampling_menu.variable.get()
    if text == '':
      return
    elif text == 'full data':
      cell_size = (1,1,1)
    else:
      cell_size = map(int, text.split())
      if len(cell_size) == 1:
        cell_size = cell_size * 3

  # ---------------------------------------------------------------------------
  #
  def use_gui_settings(self, data_region):

    pass

# -----------------------------------------------------------------------------
#
def size_text(size):

  if size[1] == size[0] and size[2] == size[0]:
    t = u'%d<sup>3</sup>' % (size[0],)       # Superscript 3
  else:
    t = '%d %d %d' % tuple(size)
  return t

# -----------------------------------------------------------------------------
#
def step_text(step):

  if step[1] == step[0] and step[2] == step[0]:
    t = '%d' % (step[0],)
  else:
    t = '%d %d %d' % tuple(step)
  return t

# -----------------------------------------------------------------------------
# Check if text represents a different vector value.
#
def vector_value(text, v, allow_singleton = False):

    vfields = text.split()
    if allow_singleton and len(vfields) == 1:
      vfields *= 3
    nv = list(v)
    if len(vfields) == 3:
      for a in range(3):
        if vfields[a] != float_format(v[a], 5):
          nv[a] = string_to_float(vfields[a], v[a])
    if nv == list(v):
      return v
    return tuple(nv)

# -----------------------------------------------------------------------------
#
def vector_value_text(vsize, precision = 5):

  if vsize[1] == vsize[0] and vsize[2] == vsize[0]:
    vst = float_format(vsize[0],precision)
  else:
    vst = ' '.join([float_format(vs,precision) for vs in vsize])
  return vst

# -----------------------------------------------------------------------------
# User interface for placement of data array in xyz coordinate space.
# Displays origin, voxel size, cell angles (for skewed x-ray data), rotation.
#
class Coordinates_Panel(PopupPanel):

  name = 'Coordinates'           # Used in feature menu.
  
  def __init__(self, dialog, parent):

    self.dialog = dialog

    PopupPanel.__init__(self, parent)

    frame = self.frame
    frame.columnconfigure(0, weight = 1)

    row = 0

    hf = Tkinter.Frame(frame)
    hf.grid(row = row, column = 0, sticky = 'ew')
    hf.columnconfigure(1, weight = 1)
    row += 1

    ostext = 'Placement of data array in x,y,z coordinate space:'
    osh = Tkinter.Label(hf, text = ostext)
    osh.grid(row = 0, column = 0, sticky = 'w')
    
    b = self.make_close_button(hf)
    b.grid(row = 0, column = 1, sticky = 'e')
    
    osf = Tkinter.Frame(frame)
    osf.grid(row = row, column = 0, sticky = 'w')
    row += 1

    org = Hybrid.Entry(osf, 'Origin index ', 20)
    org.frame.grid(row = 0, column = 0, sticky = 'e')
    self.origin = org.variable
    org.entry.bind('<KeyPress-Return>', dialog.redisplay_cb)

    orb = Tkinter.Button(osf, text = 'center',
                         command = self.center_origin_cb)
    orb.grid(row = 0, column = 1, sticky = 'w')

    orb = Tkinter.Button(osf, text = 'reset',
                         command = self.reset_origin_cb)
    orb.grid(row = 0, column = 2, sticky = 'w')

    vs = Hybrid.Entry(osf, 'Voxel size ', 20)
    vs.frame.grid(row = 1, column = 0, sticky = 'e')
    self.voxel_size = vs.variable
    vs.entry.bind('<KeyPress-Return>', dialog.redisplay_cb)

    srb = Tkinter.Button(osf, text = 'reset',
                         command = self.reset_voxel_size_cb)
    srb.grid(row = 1, column = 2, sticky = 'w')

    ca = Hybrid.Entry(osf, 'Cell angles ', 20)
    ca.frame.grid(row = 2, column = 0, sticky = 'e')
    self.cell_angles = ca.variable
    ca.entry.bind('<KeyPress-Return>', dialog.redisplay_cb)

    rx = Hybrid.Entry(osf, 'Rotation axis ', 20)
    rx.frame.grid(row = 3, column = 0, sticky = 'e')
    self.rotation_axis = rx.variable
    rx.entry.bind('<KeyPress-Return>', dialog.redisplay_cb)

    ra = Hybrid.Entry(osf, ' angle ', 5)
    ra.frame.grid(row = 3, column = 1, columnspan = 2, sticky = 'w')
    self.rotation_angle = ra.variable
    ra.entry.bind('<KeyPress-Return>', dialog.redisplay_cb)

  # ---------------------------------------------------------------------------
  #
  def update_panel_widgets(self, data_region):

    if data_region == None:
      self.update_origin(None)
      self.update_voxel_size(None)
      self.update_cell_angles(None)
      self.update_rotation(None)
    else:
      data = data_region.data
      self.update_origin(data.xyz_to_ijk((0,0,0)))
      self.update_voxel_size(data.step)
      self.update_cell_angles(data.cell_angles)
      self.update_rotation(data.rotation)

  # ---------------------------------------------------------------------------
  #
  def update_origin(self, index_origin):

    origin = '' if index_origin is None else vector_value_text(index_origin)
    self.origin.set(origin)

  # ---------------------------------------------------------------------------
  #
  def update_voxel_size(self, xyz_step):

    if xyz_step is None:
      vsize = ''
    else:
      vsize = vector_value_text(xyz_step)
    self.voxel_size.set(vsize)

  # ---------------------------------------------------------------------------
  #
  def update_cell_angles(self, cell_angles):

    if cell_angles is None:
      ca = ''
    else:
      ca = vector_value_text(cell_angles)
    self.cell_angles.set(ca)

  # ---------------------------------------------------------------------------
  #
  def update_rotation(self, rotation):

    if rotation is None:
      axis, angle = (0,0,1), 0
    else:
      import Matrix
      axis, angle = Matrix.rotation_axis_angle(rotation)
    raxis = ' '.join([float_format(x,5) for x in axis])
    rangle = float_format(angle,5)
    self.rotation_axis.set(raxis)
    self.rotation_angle.set(rangle)

  # ---------------------------------------------------------------------------
  #
  def use_gui_settings(self, data_region):

    data = data_region.data
    self.use_origin_from_gui(data)
    self.use_step_from_gui(data)
    self.use_cell_angles_from_gui(data)
    self.use_rotation_from_gui(data)

  # ---------------------------------------------------------------------------
  #
  def use_origin_from_gui(self, data):

    dorigin = data.xyz_to_ijk((0,0,0))
    origin = vector_value(self.origin.get(), dorigin, allow_singleton = True)
    if origin != dorigin:
      xyz_origin = [x0-x for x0,x in zip(data.ijk_to_xyz((0,0,0)),data.ijk_to_xyz(origin))]
      data.set_origin(xyz_origin)
      self.redraw_regions(data)
      self.dialog.message('Set new origin.')

  # ---------------------------------------------------------------------------
  #
  def use_step_from_gui(self, data):

    vsize = vector_value(self.voxel_size.get(), data.step,
                         allow_singleton = True)
    if vsize != data.step:
      if min(vsize) <= 0:
        from chimera.replyobj import warning
        warning('Voxel size must be positive, got %g,%g,%g.' % vsize)
        return
      # Preserve index origin.
      index_origin = data.xyz_to_ijk((0,0,0))
      data.set_step(vsize)
      xyz_origin = [x0-x for x0,x in zip(data.ijk_to_xyz((0,0,0)),data.ijk_to_xyz(index_origin))]
      data.set_origin(xyz_origin)
      self.redraw_regions(data)
      self.dialog.message('Set new voxel size.')

  # ---------------------------------------------------------------------------
  #
  def use_cell_angles_from_gui(self, data):

    cell_angles = vector_value(self.cell_angles.get(), data.cell_angles,
                               allow_singleton = True)
    if [a for a in cell_angles if a <= 0 or a >= 180]:
      self.dialog.message('Cell angles must be between 0 and 180 degrees')
      return
    if cell_angles != data.cell_angles:
      data.set_cell_angles(cell_angles)
      self.redraw_regions(data)
      self.dialog.message('Set new cell angles.')

  # ---------------------------------------------------------------------------
  #
  def use_rotation_from_gui(self, data):

    if data.rotation == ((1,0,0),(0,1,0),(0,0,1)):
      axis, angle = (0,0,1), 0
    else:
      import Matrix
      axis, angle = Matrix.rotation_axis_angle(data.rotation)

    naxis = vector_value(self.rotation_axis.get(), axis)
    if naxis == (0,0,0):
      self.dialog.message('Rotation axis must be non-zero')
      return

    if self.rotation_angle.get() != float_format(angle, 5):
      nangle = string_to_float(self.rotation_angle.get(), angle)
    else:
      nangle = angle

    if naxis != axis or nangle != angle:
      import Matrix
      r = Matrix.rotation_from_axis_angle(naxis, nangle)
      data.set_rotation(r)
      self.redraw_regions(data)
      self.dialog.message('Set new rotation.')

  # ---------------------------------------------------------------------------
  #
  def redraw_regions(self, data):

    from volume import regions_using_data
    drlist = regions_using_data(data)
    for dr in drlist:
      if dr.shown():
        dr.show()

  # ---------------------------------------------------------------------------
  #
  def center_origin_cb(self):

    v = active_volume()
    if v is None:
      return

    index_origin = [0.5*(s-1) for s in v.data.size]
    self.update_origin(index_origin)
    self.dialog.redisplay_needed_cb()

  # ---------------------------------------------------------------------------
  #
  def reset_origin_cb(self):

    v = active_volume()
    if v is None:
      return

    data = v.data
    # Use original index origin with original step
    data.set_origin(data.original_origin)
    step = data.step
    data.set_step(data.original_step)
    index_origin = data.xyz_to_ijk((0,0,0))
    data.set_step(step)         # Now restore step
    self.update_origin(index_origin)
    self.dialog.redisplay_needed_cb()

  # ---------------------------------------------------------------------------
  #
  def reset_voxel_size_cb(self):

    data_region = active_volume()
    if data_region == None:
      return

    data = data_region.data
    # Preserve index origin.
    index_origin = data.xyz_to_ijk((0,0,0))
    data.set_step(data.original_step)
    self.update_voxel_size(data.original_step)
    xyz_origin = [x0-x for x0,x in zip(data.ijk_to_xyz((0,0,0)),data.ijk_to_xyz(index_origin))]
    data.set_origin(xyz_origin)
    self.dialog.redisplay_needed_cb()

# -----------------------------------------------------------------------------
# User interface for setting display style: surface, mesh, solid.
#
class Display_Style_Panel(PopupPanel):

  name = 'Display style'           # Used in feature menu.
  
  def __init__(self, dialog, parent):

    self.dialog = dialog

    PopupPanel.__init__(self, parent)
    
    frame = self.frame

    from PyQt5.QtWidgets import QHBoxLayout, QLabel, QRadioButton, QButtonGroup
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(0,0,0,0)
    
    sl = QLabel('Style', frame)
    layout.addWidget(sl)

    self.button_group = bg = QButtonGroup(frame)
    bg.buttonClicked.connect(self.representation_changed_cb)
    
    initial_style = 'surface'
    self.buttons = bt = {}
    for style in ('surface', 'mesh', 'image'):
        bt[style] = b = QRadioButton(style, frame)
        b.setChecked(style == initial_style)
        layout.addWidget(b)
        bg.addButton(b)

    layout.addStretch(1)

  def get_repr(self):
      cb = self.button_group.checkedButton()
      style = cb.text()
      if style == 'image':
          style = 'solid'
      return style
  def set_repr(self, repr):
      if repr == 'solid':
          repr = 'image'
      self.buttons[repr].setChecked(True)
  representation = property(get_repr, set_repr)
  
  # ---------------------------------------------------------------------------
  # Notify all panels that representation changed so they can update gui if
  # it depends on the representation.
  #
  def representation_changed_cb(self):

      d = self.dialog
      d.representation_changed(self.representation)
      d.redisplay_needed_cb()
  
  # ---------------------------------------------------------------------------
  #
  def update_panel_widgets(self, data_region):

    if data_region and data_region.representation:
      self.representation = data_region.representation
    
  # ---------------------------------------------------------------------------
  #
  def use_gui_settings(self, data_region):

    data_region.representation = self.representation

# -----------------------------------------------------------------------------
# User interface for adjusting thresholds and colors.
#
class Thresholds_Panel(PopupPanel):

  name = 'Threshold and Color'           # Used in feature menu.
  
  def __init__(self, dialog, parent):

    self.dialog = dialog

    PopupPanel.__init__(self, parent)

    self.histogram_height = 64
    self.histogram_panes = []
    self.histogram_table = {}           # maps Volume to Histogram_Pane
    self.active_hist = None             # Histogram_Pane
    self.active_order = []              # Histogram_Panes
    self.active_color = 'white'
    self.delayed_update = None

    frame = self.frame

    from PyQt5.QtWidgets import QVBoxLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton
    from PyQt5.QtCore import Qt

    layout = QVBoxLayout(frame)
    layout.setContentsMargins(0,0,0,0)
    layout.setSpacing(0)
    
    # Histograms frame
    self.histograms_frame = hf = QFrame(frame)
    layout.addWidget(hf, stretch=1)
    self.histograms_layout = hl = QVBoxLayout(hf)
    hl.setContentsMargins(0,0,0,0)
    hl.setSpacing(0)
    hl.addStretch(1)
    
#    b = self.make_close_button(frame)
#    b.grid(row = row, column = 1, sticky = 'e')

    # Range and color line.
    rcf = QFrame(frame)
    layout.addWidget(rcf)
    rclayout = QHBoxLayout(rcf)
    rclayout.setContentsMargins(0,0,0,0)
    
    self.range_label = rh = QLabel('Range', rcf)
    rclayout.addWidget(rh)
    
    self.data_range = rn = QLabel('? - ?', rcf)
    rclayout.addWidget(rn)
#    rn['font'] = non_bold_font(frame)    # Use bold only on headings.
    
    lh = QLabel('Level', rcf)
    rclayout.addWidget(lh)
    rclayout.addSpacing(-5)	# Reduce padding to following entry field

    self.threshold = le = QLineEdit('', rcf)
    le.setMaximumWidth(40)
    le.returnPressed.connect(self.threshold_entry_enter_cb)
    rclayout.addWidget(le)

    ch = QLabel(rcf, text = 'Color')
    rclayout.addWidget(ch)
    rclayout.addSpacing(-10)	# Reduce padding to following color button
    
    self.color = cl = QPushButton(rcf)
    cl.setMaximumSize(16,16)
    cl.setAttribute(Qt.WA_LayoutUsesWidgetRect) # Avoid extra padding on Mac
    cl.clicked.connect(self.show_color_chooser)
    rclayout.addWidget(cl)    

    rclayout.addStretch(1)

    # Configure widgets for surface representation.
    self.representation_changed('surface')

    self.update_panel_widgets(None)
    
    add_volume_closed_callback(self.dialog.session, self.data_closed_cb)

  # ---------------------------------------------------------------------------
  # Create histogram for data region if needed.
  #
  def add_histogram_pane(self, data_region):

    dr = data_region
    hptable = self.histogram_table
    if dr in hptable:
      return

    same_id = [v for v in hptable.keys() if v is not None and v.id == dr.id]
    if same_id:
      # Replace entry with same id number, for volume series
      v = same_id[0]
      hp = hptable[v]
      del hptable[v]
    elif None in hptable:
      hp = hptable[None]                # Reuse unused histogram
      del hptable[None]
    elif len(hptable) >= self.maximum_histograms():
      hp = self.active_order[-1]        # Reuse least recently active histogram
      del hptable[hp.data_region]
    else:
      # Make new histogram
      hp = Histogram_Pane(self.dialog, self.histograms_frame,
                          self.histogram_height,
                          self.set_threshold_and_color_widgets)
      self.histograms_layout.addWidget(hp.frame)
      self.histogram_panes.append(hp)

    hp.set_data_region(dr)
    hptable[dr] = hp
    self.set_active_data(hp)

  # ---------------------------------------------------------------------------
  # Switch histogram threshold markers between vertical
  # lines or piecewise linear function for surfaces or solid.
  #
  def representation_changed(self, rep):

    v = self.dialog.active_volume
    if v:
      hp = self.histogram_table.get(v, None)
      if hp:
        hp.solid_mode(rep == 'solid')
  
  # ---------------------------------------------------------------------------
  #
  def data_closed_cb(self, volumes):

    hptable = self.histogram_table
    for v in tuple(volumes):
      if v in hptable:
        self.close_histogram_pane(hptable[v])
  
  # ---------------------------------------------------------------------------
  #
  def close_histogram_pane(self, hp):

    self.histogram_panes.remove(hp)
    del self.histogram_table[hp.data_region]
    self.histograms_layout.removeWidget(hp.frame)
    hp.close()
    
    if self.active_hist == hp:
      self.active_hist = None
    if hp in self.active_order:
      self.active_order.remove(hp)
    if len(self.histogram_table) == 0:
      self.add_histogram_pane(None)

  # ---------------------------------------------------------------------------
  #
  def max_histograms_cb(self, event = None):

    hptable = self.histogram_table
    if len(hptable) <= 1:
      return

    h = self.maximum_histograms()
    while len(hptable) > h:
      hp = self.active_order.pop()
      self.close_histogram_pane(hp)

  # ---------------------------------------------------------------------------
  #
  def maximum_histograms(self):

    if not hasattr(self.dialog, 'display_options_panel'):
        # return 1
        return 5
    dop = self.dialog.display_options_panel
    h = max(1, integer_variable_value(dop.max_histograms, 1))
    return h

  # ---------------------------------------------------------------------------
  #
  def update_panel_widgets(self, volume, activate = True):

    if activate:
      if volume or len(self.histogram_table) == 0:
        self.add_histogram_pane(volume)
    
    if volume is None:
      return
    
    hp = self.histogram_table.get(volume, None)
    if hp is None:
      return

#    hp.update_threshold_gui(self.dialog.message)
    hp.update_threshold_gui(None)

    if activate or hp.data_region is self.dialog.active_volume:
      self.set_active_data(hp)
      self.set_threshold_and_color_widgets(hp)
      self.update_data_range(volume)

  # ---------------------------------------------------------------------------
  #
  def update_histograms(self, data_region, read_matrix = True):

    hp = self.histogram_table.get(data_region, None)
    if hp:
      hp.update_histogram(read_matrix, self.dialog.message)
      if data_region is active_volume(self.dialog.session):
        self.update_data_range(data_region)

  # ---------------------------------------------------------------------------
  #
  def update_data_range(self, volume = None, delay = 0.5):

    # Delay data range update so graphics window update is not slowed when
    # flipping through data planes.
    delay = 0
    if delay > 0:
      f = self.frame
      if not self.delayed_update is None:
        f.after_cancel(self.delayed_update)
      def update_cb(s=self):
        s.delayed_update = None
        s.update_data_range(delay = 0)
      self.delayed_update = f.after(int(delay*1000), update_cb)
      return

    if volume is None:
      volume = active_volume()
      if volume is None:
        return

    s = volume.matrix_value_statistics(read_matrix = False)
    if s is None or s.minimum is None or s.maximum is None:
      min_text = max_text = '?'
    else:
      min_text = float_format(s.minimum, 3)
      max_text = float_format(s.maximum, 3)
    self.data_range.setText('%s - %s' % (min_text, max_text))

    self.range_label.setToolTip('value type %s' % str(volume.data.value_type))

  # ---------------------------------------------------------------------------
  #
  def update_panel_ijk_bounds(self, ijk_min, ijk_max, ijk_step):

    hp = self.active_histogram()
    if hp:
      hp.update_size_and_step((ijk_min, ijk_max, ijk_step))

  # ---------------------------------------------------------------------------
  #
  def threshold_entry_enter_cb(self):

    hp = self.active_histogram()
    if hp is None:
      return

    markers, m = hp.selected_histogram_marker()
    if m == None:
      return

    threshold = m.xy[0]
    te = self.threshold.text()
    if float_format(threshold, 3) != te:
      try:
        t = float(te)
      except ValueError:
        return
      m.xy = (t, m.xy[1])
      markers.update_plot()

      self.dialog.redisplay_cb()

  # ---------------------------------------------------------------------------
  #
  def show_color_chooser(self):
      from PyQt5.QtWidgets import QColorDialog
      from PyQt5.QtGui import QColor, QPalette
      from PyQt5.QtCore import Qt
      cd = QColorDialog(self.frame)
      cd.setOptions(QColorDialog.ShowAlphaChannel)
      bg_color = self.color.palette().color(QPalette.Window)
      cd.setCurrentColor(bg_color)
      cd.colorSelected.connect(self.color_changed_cb)
      cd.show()
      
  # ---------------------------------------------------------------------------
  #
  def color_changed_cb(self, color):

    hp = self.active_histogram()
    if hp is None:
      return
    
    markers, m = hp.selected_histogram_marker()
    if m:
      rgba = (color.redF(), color.greenF(), color.blueF(), color.alphaF())
      m.set_color(rgba, markers.canvas)	# Set histogram marker color
      from .histogram import hex_color_name
      self.color.setStyleSheet('background-color: %s' % hex_color_name(rgba[:3])) # set button color
    self.dialog.redisplay_needed_cb()

  # ---------------------------------------------------------------------------
  #
  def set_threshold_and_color_widgets(self, hp):

    if hp != self.active_histogram():
      return
    
    markers, m = hp.selected_histogram_marker()
    if m:
      threshold = m.xy[0]
      t_str = float_format(threshold, 3)
      self.threshold.setText(t_str)
      from .histogram import hex_color_name
      self.color.setStyleSheet('background-color: %s' % hex_color_name(m.rgba[:3]))

  # ---------------------------------------------------------------------------
  #
  def active_histogram(self):

    return self.active_hist

  # ---------------------------------------------------------------------------
  #
  def set_active_data(self, hp):

    a = self.active_hist
#    if a and a.frame:
#      a.data_name['background'] = self.frame['background']
    self.active_hist = hp
    if hp and hp.frame:
#      hp.data_name['background'] = self.active_color
      ao = self.active_order
      if hp in ao:
        ao.remove(hp)
      ao.insert(0, hp)
    
  # ---------------------------------------------------------------------------
  #
  def histogram_shown(self, data_region):

    hp = self.histogram_table.get(data_region, None)
    return hp and hp.histogram_shown
    
  # ---------------------------------------------------------------------------
  #
  def use_gui_settings(self, data_region):

    hp = self.histogram_table.get(data_region, None)
    if hp and hp.histogram_shown:
      hp.set_threshold_parameters_from_gui()
  
# -----------------------------------------------------------------------------
# Manages histogram and heading with data name, step size, shown indicator,
# and map close button.
#
class Histogram_Pane:

  def __init__(self, dialog, parent, histogram_height,
               show_threshold_and_color_cb):

    self.dialog = dialog
    self.data_region = None
    self.show_threshold_and_color_cb = show_threshold_and_color_cb
    self.histogram_data = None
    self.histogram_size = None
    self.delayed_update = None

    from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QMenu
    from PyQt5.QtGui import QPixmap, QIcon
    from PyQt5.QtCore import Qt, QSize

    self.frame = f = QFrame(parent)
    flayout = QVBoxLayout(f)
    flayout.setContentsMargins(0,0,0,0)
    flayout.setSpacing(0)
    
    df = QFrame(f)
    flayout.addWidget(df)
    layout = QHBoxLayout(df)
    layout.setContentsMargins(0,0,0,0)
    layout.setSpacing(10)

    self.data_name = nm = QLabel(df)
    layout.addWidget(nm)
#    nm.bind("<ButtonPress>", self.select_data_cb)

    self.size = sz = QLabel(df)
    layout.addWidget(sz)
#    sz.bind("<ButtonPress>", self.select_data_cb)

    sl = QLabel('step', df)
    layout.addWidget(sl)
    layout.addSpacing(-7)
    self.data_step = dsm = QPushButton(df)
    dsm.setStyleSheet('padding-left: 4px; padding-right: 0px;')
    dsm.setMaximumSize(30,20)
    # TODO: Need to hide the menu indicator.  Can set it to 1x1 pixel image with style sheet.
    dsm.setAttribute(Qt.WA_LayoutUsesWidgetRect) # Avoid extra padding on Mac
    sm = QMenu()
    for step in (1,2,4,8,16):
        sm.addAction('%d' % step, lambda s=step: self.data_step_cb(s))
    dsm.setMenu(sm)
    layout.addWidget(dsm)

    self.shown = sh = QPushButton(df)
    sh.setAttribute(Qt.WA_LayoutUsesWidgetRect) # Avoid extra padding on Mac
    sh.setMaximumSize(20,20)
    sh.setCheckable(True)
    sh.setFlat(True)
    sh.setStyleSheet('QPushButton {background-color: transparent;}')
    from os.path import join, dirname
    shpix = QPixmap(join(dirname(__file__), 'shown.png'))
    sh.setIcon(QIcon(shpix))
    sh.setIconSize(QSize(20,20))
    sh.clicked.connect(self.show_cb)
    layout.addWidget(sh)
    sh.setToolTip('Display or undisplay data')
    self.shown_handlers = []

    layout.addStretch(1)

    cb = QPushButton(df)
    cb.setAttribute(Qt.WA_LayoutUsesWidgetRect) # Avoid extra padding on Mac
    cb.setMaximumSize(20,20)
    cb.setFlat(True)
    layout.addWidget(cb)
    cbpix = QPixmap(join(dirname(__file__), 'close.png'))
    cb.setIcon(QIcon(cbpix))
    cb.setIconSize(QSize(20,20))
    cb.clicked.connect(self.close_map_cb)
    cb.setToolTip('Close data set')

    h = self.make_histogram(f, histogram_height, new_marker_color = (1,1,1,1))
    flayout.addWidget(h)

  # ---------------------------------------------------------------------------
  #
  def set_data_region(self, data_region):

    self.data_region = data_region
    self.histogram_shown = False
    self.histogram_data = None
    self.show_data_name()
    # if data_region:
    #   if not self.shown_handlers:
    #     from chimera import triggers, openModels as om
    #     h = [(tset, tname, tset.addHandler(tname, self.check_shown_cb, None))
    #          for tset, tname in ((triggers, 'Model'),
    #                              (om.triggers, om.ADDMODEL))]
    #     self.shown_handlers = h

    new_marker_color = data_region.default_rgba if data_region else (1,1,1,1)
    self.surface_thresholds.new_marker_color = new_marker_color
    self.solid_thresholds.new_marker_color = saturate_rgba(new_marker_color)

  # ---------------------------------------------------------------------------
  #
  def show_data_name(self):

    name = self.data_region.name_with_id() if self.data_region else ''
    self.data_name.setText(name)

  # ---------------------------------------------------------------------------
  #
  def close_map_cb(self, event = None):

    v = self.data_region
    if v:
        self.dialog.session.models.close([v])

  # ---------------------------------------------------------------------------
  #
  def make_histogram(self, frame, histogram_height, new_marker_color):

    cborder = 2
    #
    # set highlight thickness = 0 so line in column 0 is visible.
    #
    from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
    from PyQt5.QtCore import Qt

    class Canvas(QGraphicsView):
        def __init__(self, parent):
            QGraphicsView.__init__(self, parent)
            self.click_callbacks = []
            self.drag_callbacks = []
        def resizeEvent(self, event):
            # Rescale histogram when window resizes
            self.fitInView(self.sceneRect())
            QGraphicsView.resizeEvent(self, event)
        def mousePressEvent(self, event):
            for cb in self.click_callbacks:
                cb(event)
        def mouseMoveEvent(self, event):
            for cb in self.drag_callbacks:
                cb(event)

    self.canvas = gv = Canvas(frame)
    gv.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    gv.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self.scene = gs = QGraphicsScene(gv)
    gs.setSceneRect(0, 0, 500, 100)
    gv.setScene(gs)
    
#    c = Tkinter.Canvas(frame, height = histogram_height,
#                       borderwidth = cborder, relief = 'sunken',
#                       highlightthickness = 0)

    from .histogram import Histogram, Markers
    self.histogram = Histogram(gv, gs)
    self.histogram_shown = False

    st = Markers(gv, gs, 'line', new_marker_color, 0, self.select_marker_cb)
    self.surface_thresholds = st

    new_solid_marker_color = saturate_rgba(new_marker_color)
    sdt = Markers(gv, gs, 'box', new_solid_marker_color, 1, self.select_marker_cb)
    self.solid_thresholds = sdt

#    c.bind('<Configure>', self.canvas_resize_cb)
#    c.bind("<ButtonPress>", self.select_data_cb, add = True)
#    c.bind("<ButtonPress-1>", self.select_data_cb, add = True)

#    gv.setStyleSheet('background-color: #eff')
    return gv

  # ---------------------------------------------------------------------------
  #
  def canvas_resize_cb(self, event = None):

    if self.histogram_shown:
      self.update_histogram(read_matrix = False,
                            message_cb = self.dialog.message,
                            resize = True)

  # ---------------------------------------------------------------------------
  #
  def select_data_cb(self, event = None):

    dr = self.data_region
    if dr:
      d = self.dialog
      if dr != d.active_volume:
        d.display_volume_info(dr)
      d.redisplay_needed_cb()

  # ---------------------------------------------------------------------------
  #
  def select_marker_cb(self):

    self.select_data_cb()
    self.show_threshold_and_color_cb(self)

  # ---------------------------------------------------------------------------
  #
  def data_step_cb(self, step):

    self.data_step.setText('%d' % step)

    dr = self.data_region
    if dr is None or dr.region is None:
      return

    ijk_step = [step]
    if len(ijk_step) == 1:
      ijk_step = ijk_step * 3

    if tuple(ijk_step) == tuple(dr.region[2]):
      return

    ijk_min, ijk_max = dr.region[:2]
    dr.new_region(ijk_min, ijk_max, ijk_step, adjust_step = False, show = True)
    d = self.dialog
    if dr != d.active_volume:
      d.display_volume_info(dr)
#    d.redisplay_needed_cb()

  # ---------------------------------------------------------------------------
  #
  def show_cb(self):

    dr = self.data_region
    if dr is None:
      return

    show = self.shown.isChecked()
    for m in self.data_region.models():
      m.display = show

    self.update_shown_icon()

    if show:
      self.select_data_cb()

  # ---------------------------------------------------------------------------
  #
  def check_shown_cb(self, trigger, x, changes):

    from chimera import openModels
    if trigger == 'Model':
      if self.data_region.representation == 'solid':
        from _volume import Volume_Model
        if [m for m in changes.deleted if isinstance(m, Volume_Model)]:
          self.update_shown_icon()
      if not [m for m in self.data_region.models()
              if m in changes.modified or m in changes.created]:
        return
      if 'name changed' in changes.reasons:
        self.show_data_name()
      if 'display changed' in changes.reasons:
        self.update_shown_icon()
    elif trigger == openModels.ADDMODEL:
      self.update_shown_icon()
      
  # ---------------------------------------------------------------------------
  #
  def update_shown_icon(self):

    v = self.data_region
    if v is None:
      return

    shown = v.shown()
#    if shown == self.shown.isChecked():
#        return
    fname = 'shown.png' if shown else 'hidden.png'
    from os.path import join, dirname
    from PyQt5.QtGui import QPixmap, QIcon
    shpix = QPixmap(join(dirname(__file__), fname))
    s = self.shown
    s.setIcon(QIcon(shpix))
    s.setChecked(shown)
      
  # ---------------------------------------------------------------------------
  #
  def solid_mode(self, solid):

    self.solid_thresholds.show(solid)
    self.surface_thresholds.show(not solid)
    self.show_threshold_and_color_cb(self)

  # ---------------------------------------------------------------------------
  #
  def selected_histogram_marker(self):

    if self.solid_thresholds.shown:
      markers = self.solid_thresholds
    elif self.surface_thresholds.shown:
      markers = self.surface_thresholds
    else:
      return None, None

    return markers, markers.selected_marker()

  # ---------------------------------------------------------------------------
  #
  def update_threshold_gui(self, message_cb):

    read_matrix = False
    self.update_histogram(read_matrix, message_cb)

    self.update_size_and_step()
    self.update_shown_icon()

    self.plot_surface_levels()
    self.plot_solid_levels()
    rep = self.data_region.representation
    if rep is None:
      rep = self.dialog.display_style_panel.representation
    self.solid_mode(rep == 'solid')
    
  # ---------------------------------------------------------------------------
  #
  def update_size_and_step(self, region = None):

    if region is None:
      dr = self.data_region
      if dr is None:
        return
      region = dr.region

    ijk_min, ijk_max, ijk_step = region
    size = [a-b+1 for a,b in zip(ijk_max, ijk_min)]
    self.size.setText(size_text(size))

    step = step_text(ijk_step)
    ds = self.data_step
#    if not step in ds.values:
#      ds.add_entry(step)
    # TODO: Block step change callback.
    ds.setText(step)
    
  # ---------------------------------------------------------------------------
  #
  def plot_surface_levels(self):

    v = self.data_region
    if v is None:
      return

    from .histogram import Marker
    surf_markers = [Marker((t,0), c) for t,c in zip(v.surface_levels, v.surface_colors)]
    self.surface_thresholds.set_markers(surf_markers)
    
  # ---------------------------------------------------------------------------
  #
  def plot_solid_levels(self):

    v = self.data_region
    if v is None:
      return

    from .histogram import Marker
    solid_markers = [Marker(ts, c) for ts, c in zip(v.solid_levels, v.solid_colors)]
    self.solid_thresholds.set_markers(solid_markers)
    
  # ---------------------------------------------------------------------------
  #
  def update_histogram(self, read_matrix, message_cb, resize = False,
                       delay = 0.5):

    v = self.data_region
    if v is None:
      return

    # Delay histogram update so graphics window update is not slowed when
    # flipping through data planes.
    delay = 0
    if delay > 0:
      f = self.frame
      if not self.delayed_update is None:
        f.after_cancel(self.delayed_update)
      def update_cb(s=self, rm=read_matrix, m=message_cb, rz=resize):
        s.delayed_update = None
        s.update_histogram(rm, m, rz, delay = 0)
      self.delayed_update = f.after(int(delay*1000), update_cb)
      return

    s = v.matrix_value_statistics(read_matrix)
    if s is None:
      return

    if s == self.histogram_data and not resize:
      return

    bins = self.histogram_bins()
    if resize and bins == self.histogram_size and s == self.histogram_data:
      return    # Histogram size and data unchanged.

    if message_cb:
        message_cb('Showing histogram')
    self.histogram_data = s
    counts = s.bin_counts(bins)
    h = self.histogram
    from numpy import log
    h.show_data(log(counts + 1))
    self.histogram_shown = True
    self.histogram_size = bins
    if message_cb:
        message_cb('')
    first_bin_center, last_bin_center, bin_size = s.bin_range(bins)
    self.solid_thresholds.set_user_x_range(first_bin_center, last_bin_center)
    self.surface_thresholds.set_user_x_range(first_bin_center, last_bin_center)
  
  # ---------------------------------------------------------------------------
  #
  def histogram_bins(self):

      return int(self.scene.sceneRect().width())

#     c = self.canvas
#     s = c.size()
#     cborder = 0
#     hwidth = s.width() - 2*cborder
# #    if hwidth <= 1:
# #      c.update_idletasks()
# #      hwidth = s.width() - 2*cborder
#     if hwidth <= 1:
#       hwidth = 300
#     hheight = s.height()
#     bins = hwidth - 1
#     hbox = (cborder, cborder + 5, cborder + bins - 1, cborder + hheight - 5)
#     self.surface_thresholds.set_canvas_box(hbox)
#     self.solid_thresholds.set_canvas_box(hbox)
#     return bins

  # ---------------------------------------------------------------------------
  #
  def set_threshold_parameters_from_gui(self):

    v = self.data_region
    if v is None:
      return
    
    markers = self.surface_thresholds.markers
    v.surface_levels = [m.xy[0] for m in markers]
    v.surface_colors = [m.rgba for m in markers]
    markers = self.solid_thresholds.markers
    v.solid_levels = [m.xy for m in markers]
    v.solid_colors = [m.rgba for m in markers]

  # ---------------------------------------------------------------------------
  # Delete widgets and references to other objects.
  #
  def close(self):

    for tset, tname, h in self.shown_handlers:
      tset.deleteHandler(tname, h)
    self.shown_handlers = []

    self.dialog = None
    self.data_region = None
    self.histogram_data = None

    # Suprisingly need to set parent to None or the frame and children are still shown.
    self.frame.setParent(None)
    self.frame.destroy()
    self.frame = None

    self.canvas = None
    self.scene = None
    self.histogram = None

# -----------------------------------------------------------------------------
# User interface for adjusting brightness and transparency.
#
class Brightness_Transparency_Panel(PopupPanel):

  name = 'Brightness and Transparency'           # Used in feature menu.
  
  def __init__(self, dialog, parent):

    self.dialog = dialog

    PopupPanel.__init__(self, parent)
    
    frame = self.frame
    frame.columnconfigure(0, weight = 1)
    row = 0

    bf = Hybrid.Logarithmic_Scale(frame, 'Brightness ', .01, 10, 1, '%.2g')
    bf.frame.grid(row = row, column = 0, sticky = 'ew')
    bf.callback(dialog.redisplay_needed_cb)
    bf.entry.bind('<KeyPress-Return>', dialog.redisplay_cb)
    self.surface_brightness_factor = bf

    bfs = Hybrid.Logarithmic_Scale(frame, 'Brightness ', .01, 10, 1, '%.2g')
    bfs.frame.grid(row = row, column = 0, sticky = 'ew')
    bfs.callback(dialog.redisplay_needed_cb)
    bfs.entry.bind('<KeyPress-Return>', dialog.redisplay_cb)
    self.solid_brightness_factor = bfs

    b = self.make_close_button(frame)
    b.grid(row = row, column = 1, sticky = 'e')
    row += 1

    tfs = Hybrid.Scale(frame, 'Transparency ', 0, 1, .01, 0)
    tfs.frame.grid(row = row, column = 0, sticky = 'ew')
    tfs.callback(dialog.redisplay_needed_cb)
    tfs.entry.bind('<KeyPress-Return>', dialog.redisplay_cb)
    self.transparency_factor = tfs

    tds = Hybrid.Scale(frame, 'Transparency ', 0, 1, .01, 0)
    tds.frame.grid(row = row, column = 0, sticky = 'ew')
    row += 1
    tds.callback(dialog.redisplay_needed_cb)
    tds.entry.bind('<KeyPress-Return>', dialog.redisplay_cb)
    self.transparency_depth = tds

    self.representation_changed('surface')
    
  # ---------------------------------------------------------------------------
  # Show brightness and transparency sliders appropriate for surface or solid.
  # Solid uses logarithmic transparency depth slider and surface uses linear
  # transparency factor.
  #
  def representation_changed(self, representation):

    solid = (representation == 'solid')
    place_in_grid(self.transparency_factor.frame, not solid)
    place_in_grid(self.surface_brightness_factor.frame, not solid)
    place_in_grid(self.transparency_depth.frame, solid)
    place_in_grid(self.solid_brightness_factor.frame, solid)
  
  # ---------------------------------------------------------------------------
  #
  def update_panel_widgets(self, data_region):
    
    dr = data_region
    if dr == None:
      return

    self.transparency_factor.set_value(dr.transparency_factor,
                                       invoke_callbacks = False)
    self.transparency_depth.set_value(dr.transparency_depth,
                                      invoke_callbacks = False)
    self.surface_brightness_factor.set_value(dr.surface_brightness_factor,
                                             invoke_callbacks = False)
    self.solid_brightness_factor.set_value(dr.solid_brightness_factor,
                                           invoke_callbacks = False)

  # ---------------------------------------------------------------------------
  #
  def use_gui_settings(self, data_region):

    dr = data_region
    tf = self.transparency_factor.value(default = 0)
    td = self.transparency_depth.value(default = 0)
    bf = self.surface_brightness_factor.value(default = 1)
    bfs = self.solid_brightness_factor.value(default = 1)

    dr.transparency_factor = tf      # for surface/mesh
    dr.surface_brightness_factor = bf
    dr.transparency_depth = td       # for solid
    dr.solid_brightness_factor = bfs

# -----------------------------------------------------------------------------
# User interface for selecting subregions of a data set.
#
class Named_Region_Panel(PopupPanel):

  name = 'Named regions'           # Used in feature menu.
  
  def __init__(self, dialog, parent):

    self.dialog = dialog

    PopupPanel.__init__(self, parent)
    
    frame = self.frame
    frame.columnconfigure(3, weight = 1)

    rn = Hybrid.Entry(frame, 'Named region ', 10)
    rn.frame.grid(row = 0, column = 0, sticky = 'w')
    rn.entry.bind('<KeyPress-Return>', self.region_name_cb)
    self.region_name = rn.variable

    nm = Hybrid.Menu(frame, 'Show', [])
    nm.button.configure(borderwidth = 2, relief = 'raised',
                        highlightthickness = 2)
    nm.button.grid(row = 0, column = 1, sticky = 'w')
    self.region_name_menu = nm

    rb = Hybrid.Button_Row(frame, '',
                           (('Add', self.add_named_region_cb),
                            ('Delete', self.delete_named_region_cb),
                            ))
    rb.frame.grid(row = 0, column = 2, sticky = 'w')
    
    b = self.make_close_button(frame)
    b.grid(row = 0, column = 3, sticky = 'e')

  # ---------------------------------------------------------------------------
  #
  def use_gui_settings(self, data_region):

    pass

  # ---------------------------------------------------------------------------
  #
  def update_panel_widgets(self, data_region):

    self.update_region_name_menu(data_region)
    if data_region and data_region.region:
      self.update_panel_ijk_bounds(*data_region.region)
    
  # ---------------------------------------------------------------------------
  #
  def update_panel_ijk_bounds(self, ijk_min, ijk_max, ijk_step):

    self.show_region_name(ijk_min, ijk_max)
    
  # ---------------------------------------------------------------------------
  #
  def region_name_cb(self, event):

    name = self.region_name.get()
    self.show_named_region(name)
    
  # ---------------------------------------------------------------------------
  #
  def add_named_region_cb(self):

    name = self.region_name.get()
    if not name:
      return

    data_region = active_volume()
    if data_region == None:
      return

    self.delete_named_region_cb()
    self.region_name.set(name)

    ijk_min, ijk_max, ijk_step = data_region.region
    rlist = data_region.region_list
    rlist.add_named_region(name, ijk_min, ijk_max)

    cb = lambda show=self.show_named_region, nm=name: show(name)
    self.region_name_menu.add_entry(name, cb)
    
  # ---------------------------------------------------------------------------
  #
  def show_named_region(self, name):

    dr = active_volume()
    if dr == None:
      return
    
    self.region_name.set(name)
    ijk_min, ijk_max = dr.region_list.named_region_bounds(name)
    if ijk_min == None or ijk_max == None:
      return
    dr.new_region(ijk_min, ijk_max)

  # ---------------------------------------------------------------------------
  # If region bounds has a name then show it.
  #
  def show_region_name(self, ijk_min, ijk_max):

    data_region = active_volume()
    if data_region:
      rlist = data_region.region_list
      name = rlist.find_named_region(ijk_min, ijk_max)
      if name == None:
        name = ''
      self.region_name.set(name)
    
  # ---------------------------------------------------------------------------
  #
  def delete_named_region_cb(self):

    data_region = active_volume()
    if data_region == None:
      return

    name = self.region_name.get()
    rlist = data_region.region_list
    index = rlist.named_region_index(name)
    if index == None:
      return

    rlist.remove_named_region(index)
    rnm = self.region_name_menu
    from CGLtk.Hybrid import base_menu_index
    i0 = base_menu_index(rnm)
    rnm.remove_entry(index+i0)
    self.region_name.set('')
    
  # ---------------------------------------------------------------------------
  #
  def update_region_name_menu(self, data_region):

    self.region_name.set('')
    self.region_name_menu.remove_all_entries()
    if data_region == None:
      return

    rlist = data_region.region_list
    for name in rlist.region_names():
      cb = lambda show=self.show_named_region, nm=name: show(nm)
      self.region_name_menu.add_entry(name, cb)

# -----------------------------------------------------------------------------
# User interface for showing data z planes.
#
class Plane_Panel(PopupPanel):

  name = 'Planes'           # Used in feature menu.
  
  def __init__(self, dialog, parent):

    self.dialog = dialog

    PopupPanel.__init__(self, parent)
    
    frame = self.frame

    self.last_axis = 2
    self.data_size = (1,1,1)
    self.change_plane_in_progress = False
    
    frame.columnconfigure(0, weight = 1)       # Let scale width expand
    row = 0

    ps = Hybrid.Scale(frame, 'Plane ', 0, 100, 1, 0, entry_width = 4)
    ps.frame.grid(row = row, column = 0, sticky = 'ew')
    ps.callback(self.change_plane_cb)
    ps.entry.bind('<KeyPress-Return>', self.change_plane_cb)
    self.plane = ps

    b = self.make_close_button(frame)
    b.grid(row = row, column = 1, sticky = 'e')
    row += 1

    from chimera.tkgui import windowSystem
    if windowSystem == 'aqua': xp = 9
    else: xp = 2

    cf = Tkinter.Frame(frame)
    cf.grid(row = row, column = 0, columnspan = 3, sticky = 'w')
    row += 1

    oa = Hybrid.Button_Row(cf, '', (('One', self.single_plane_cb),
                                    ('All', self.full_depth_cb)))
    oa.frame.grid(row = 0, column = 0, padx = 5, sticky = 'w')
    for b in oa.buttons:
      b.configure(padx = xp, pady = 1)

    self.axis_names = ['X', 'Y', 'Z']
    am = Hybrid.Option_Menu(cf, 'Axis', *self.axis_names)
    am.button.configure(pady = 1, indicatoron = False)
    am.frame.grid(row = 0, column = 1, sticky = 'w')
    self.axis = am.variable
    self.axis.set(self.axis_names[2], invoke_callbacks = False)
    am.add_callback(self.change_axis_cb)

    dp = Hybrid.Entry(cf, 'Depth ', 3, '1')
    dp.frame.grid(row = 0, column = 2, padx = 5, sticky = 'w')
    dp.entry.bind('<KeyPress-Return>', self.change_plane_cb)
    self.depth_var = dp.variable

    pl = Tkinter.Button(cf, text = 'Preload', padx = xp, pady = 1,
                        command = self.preload_cb)
    pl.grid(row = 0, column = 3, sticky = 'w')

    mpf = Tkinter.Frame(frame)
    mpf.grid(row = row, column = 0, sticky = 'ew')
    mpf.columnconfigure(2, weight = 1)
    row += 1
    
    mp = Hybrid.Checkbutton(mpf, 'Move planes using ', 0)
    mp.button.grid(row = 0, column = 0, sticky = 'w')
    self.move_planes = mp.variable
    mp.callback(self.move_planes_cb)

    mpm = Hybrid.Option_Menu(mpf, '', *mouse_button_names)
    mpm.variable.set('right')
    mpm.frame.grid(row = 0, column = 1, sticky = 'w')
    mpm.add_callback(self.move_planes_cb)
    self.move_planes_button = mpm.variable

    mpl = Tkinter.Label(mpf, text = ' mouse button')
    mpl.grid(row = 0, column = 2, sticky = 'w')

  # ---------------------------------------------------------------------------
  #
  def use_gui_settings(self, data_region):

    pass

  # ---------------------------------------------------------------------------
  #
  def update_panel_widgets(self, volume):

    if volume:
      r = volume.region
      if r:
        self.data_size = volume.data.size
        self.update_axis(*r)
        self.update_panel_ijk_bounds(*r)
    
  # ---------------------------------------------------------------------------
  #
  def update_panel_ijk_bounds(self, ijk_min, ijk_max, ijk_step):

    v = active_volume()

    # Set number of planes shown.
    a = self.axis_number()
    s = ijk_step[a]
    if v.showing_orthoplanes():
      d = 1
    else:
      d = max(1, ijk_max[a]/s - (ijk_min[a]+s-1)/s + 1)
    self.depth_var.set(d, invoke_callbacks = False)

    # Set scale range.
    smax = self.data_size[a]
    self.set_scale_range(smax, s)

    # Set plane scale value, unless it is due to a user slider adjustment.
    if not self.change_plane_in_progress:
      p = dict(v.shown_orthoplanes()).get(a, ijk_min[a])
      self.plane.set_value(p, invoke_callbacks = False)
    
  # ---------------------------------------------------------------------------
  #
  def update_axis(self, ijk_min, ijk_max, ijk_step):

    v = active_volume()
    if v.showing_orthoplanes():
      axis_i = v.shown_orthoplanes()
      if self.axis_number() in dict(axis_i):
        return
      axis,i = axis_i[0]
    else:
      # Set axis to one with fewest planes.
      size = [(ijk_max[a] - ijk_min[a] + 1, -a) for a in range(3)]
      size.sort()
      axis = -size[0][1]
    self.axis.set(self.axis_names[axis], invoke_callbacks = False)
    self.last_axis = axis
    
  # ---------------------------------------------------------------------------
  #
  def set_scale_range(self, size, step):

    s = self.plane
    if size is None:
      size = s.scale['to']
    pmax = max(0, size - self.depth()*step)
    s.set_range(0, pmax, step)

  # ---------------------------------------------------------------------------
  #
  def single_plane_cb(self):

    v = active_volume()
    if v is None or v.region is None:
      return

    v.set_parameters(orthoplanes_shown = (False, False, False),
                     box_faces = False, color_mode = 'auto8')
    self.depth_var.set(1, invoke_callbacks = False)
    ijk_min, ijk_max, ijk_step = v.region
    a = self.axis_number()
    p = (ijk_min[a] + ijk_max[a]) / 2
    p -= p % ijk_step[a]
    self.plane.set_value(p)
    if v.representation != 'solid':
      v.set_representation('solid')
      v.show()

  # ---------------------------------------------------------------------------
  #
  def full_depth_cb(self):

    v = active_volume()
    if v is None or v.region is None:
      return

    if v.showing_orthoplanes():
      v.set_parameters(orthoplanes_shown = (False, False, False))
      v.show()
    ijk_min, ijk_max, ijk_step = v.region
    a = self.axis_number()
    s = ijk_step[a]
    d = (v.data.size[a] + s - 1) / s
    self.depth_var.set(d)
    self.plane.set_value(0)

  # ---------------------------------------------------------------------------
  #
  def change_axis_cb(self):

    v = active_volume()
    if v is None or v.region is None:
      return

    ijk_min, ijk_max, ijk_step = v.region
    a = self.axis_number()
    step = ijk_step[a]
    max = v.data.size[a]
    self.set_scale_range(max, step)
    p = (ijk_min[a] + ijk_max[a]) / 2
    p -= p % step
    if v.showing_orthoplanes():
      oaxes = dict(v.shown_orthoplanes())
      p = dict(v.shown_orthoplanes()).get(a, p)
    self.plane.set_value(p, invoke_callbacks = False)
    self.change_plane_cb(extend_axes = [self.last_axis])
    self.last_axis = a

    # If region did not change, update plane and depth numbers for new axis.
    self.update_panel_ijk_bounds(*v.region)

  # ---------------------------------------------------------------------------
  #
  def axis_number(self):

    axis = self.axis_names.index(self.axis.get())
    return axis

  # ---------------------------------------------------------------------------
  #
  def depth(self):

    d = integer_variable_value(self.depth_var, 1)
    return d
    
  # ---------------------------------------------------------------------------
  #
  def preload_cb(self, event = None):

    v = active_volume()
    if v:
      step = v.region[2]

      # Increase map data cache size if it is smaller than preloaded data.
      isz, jsz, ksz = v.matrix_size(step = step, subregion = 'all')
      bytes =  1.2 * isz*jsz*ksz * v.data.value_type.itemsize
      from VolumeData import data_cache
      if bytes > data_cache.size:
        data_cache.resize(bytes)
        dcs = self.dialog.display_options_panel.data_cache_size
        mbytes = (1.0/2**20)*bytes
        dcs.set('%.1f' % (mbytes,), invoke_callbacks = False)

      # Load data
      v.full_matrix(step = step)
  
  # ---------------------------------------------------------------------------
  #
  def change_plane_cb(self, event = None, extend_axes = [],
                      save_in_region_queue = False):

    self.change_plane_in_progress = True
    self.change_plane(extend_axes, save_in_region_queue)
    self.change_plane_in_progress = False

  # ---------------------------------------------------------------------------
  #
  def change_plane(self, extend_axes = [], save_in_region_queue = False):

    v = active_volume()
    if v is None:
      return

    # Get plane number
    s = self.plane
    p = s.value()
    if p == None:
      return            # Scale value is non-numeric

    a = self.axis_number()
    d = self.depth()
    from volume import show_planes
    if not show_planes(v, a, p, d, extend_axes,
                       save_in_region_queue = save_in_region_queue):
      return    # Plane already shown.

    max = v.data.size[a]
    step = v.region[2][a]
    self.set_scale_range(max, step) # Update scale range.
  
  # ---------------------------------------------------------------------------
  #
  def move_planes_cb(self):

    from moveplanes import planes_mouse_mode
    if self.move_planes.get():
      button, modifiers = button_spec(self.move_planes_button.get())
      planes_mouse_mode.bind_mouse_button(button, modifiers)
    else:
      planes_mouse_mode.unbind_mouse_button()

# -----------------------------------------------------------------------------
# User interface for showing 3 orthogonal planes of one map.
#
class Orthoplane_Panel(PopupPanel):

  name = 'Orthogonal planes'           # Used in feature menu.
  
  def __init__(self, dialog, parent):

    self.dialog = dialog

    PopupPanel.__init__(self, parent)
    
    frame = self.frame
    frame.columnconfigure(0, weight = 1)       # Let scale width expand
    row = 0

    import Tkinter
    opf = Tkinter.Frame(frame)
    opf.grid(row = 0, column = 0, sticky = 'ew')
    c = 0

    opl = Tkinter.Label(opf, text='Orthoplanes ')
    opl.grid(row = 0, column = 0, sticky = 'w')
    c += 1
    self.planes = pvars = [None, None, None]
    for axis, aname in enumerate(('x','y','z')):
      pb = Hybrid.Checkbutton(opf, aname, False)
      pb.button.grid(row = 0, column = c, sticky = 'w')
      pvars[axis] = pb.variable
      pb.callback(self.show_plane_cb)
      c += 1
      Tkinter.Label(opf, text = ' ').grid(row = 0, column = c, sticky = 'w')
      c += 1

    bf = Hybrid.Checkbutton(opf, 'Box', False)
    bf.button.grid(row = 0, column = c, sticky = 'w')
    self.box_faces = bf.variable
    bf.callback(self.box_faces_cb)
    c += 1

    b = self.make_close_button(frame)
    b.grid(row = row, column = 1, sticky = 'e')
    row += 1

  # ---------------------------------------------------------------------------
  #
  def use_gui_settings(self, volume):

    pass
  
  # ---------------------------------------------------------------------------
  #
  def update_panel_widgets(self, volume):

    if volume is None:
      return

    solid = (volume.representation == 'solid')
    ro = volume.rendering_options
    box_faces = ro.box_faces
    shown = ro.orthoplanes_shown
    msize = volume.matrix_size()
    for axis in (0,1,2):
      p = bool(solid and not box_faces and (shown[axis] or msize[axis] == 1))
      self.planes[axis].set(p, invoke_callbacks = False)

    box = bool(solid and box_faces)
    self.box_faces.set(box, invoke_callbacks = False)
    
  # ---------------------------------------------------------------------------
  # If region changes to single plane, activate plane checkbutton.
  #
  def update_panel_ijk_bounds(self, ijk_min, ijk_max, ijk_step):

    self.update_panel_widgets(active_volume())

  # ---------------------------------------------------------------------------
  #
  def show_plane_cb(self):

    v = active_volume()
    if v and v.region:
      show = tuple(self.planes[axis].get() for axis in (0,1,2))
      self.show_planes(v, show)

  # ---------------------------------------------------------------------------
  #
  def show_planes(self, volume, show_xyz):

    self.box_faces.set(False, invoke_callbacks = False)
    volume.set_parameters(box_faces = False)

    n = show_xyz.count(True)
    if n == 0:          # No planes
      volume.set_parameters(orthoplanes_shown = (False, False, False),
                            color_mode = 'auto8')
      volume.expand_single_plane()
    elif n == 1:        # Single plane
      axis = show_xyz.index(True)
      ijk_min, ijk_max = [list(b) for b in volume.region[:2]]
      imid = (ijk_min[axis] + ijk_max[axis])/2
      i = dict(volume.shown_orthoplanes()).get(axis, imid)
      ijk_min[axis] = ijk_max[axis] = i
      msize = volume.matrix_size()
      for a in (0,1,2):
        if a != axis and msize[a] == 1:
          ijk_min[a] = 0
          ijk_max[a] = volume.data.size[a]-1
      volume.set_parameters(orthoplanes_shown = (False, False, False),
                            color_mode = 'auto8',
                            show_outline_box = True)
      volume.new_region(ijk_min, ijk_max, show = False)
    else:               # 2 or 3 planes
      ro = volume.rendering_options
      if ro.any_orthoplanes_shown():
        center = ro.orthoplane_positions
      else:
        ijk_min, ijk_max = volume.region[:2]
        center = tuple((a+b)/2 for a,b in zip(ijk_min, ijk_max))
      volume.expand_single_plane()
      volume.set_parameters(orthoplanes_shown = show_xyz,
                            orthoplane_positions = center,
                            color_mode = 'opaque8',
                            show_outline_box = True)
      volume.set_representation('solid')
    volume.show()
    
  # ---------------------------------------------------------------------------
  #
  def box_faces_cb(self):

    v = active_volume()
    if v is None:
      return

    if self.box_faces.get():
      v.set_representation('solid')
      v.set_parameters(box_faces = True,
                       color_mode = 'opaque8',
                       show_outline_box = True,
                       orthoplanes_shown = (False, False, False))
      v.expand_single_plane()
      v.show()
      for a in (0,1,2):
        self.planes[a].set(False, invoke_callbacks = False)
    else:
      v.set_parameters(box_faces = False, color_mode = 'auto8')
      v.show()

# -----------------------------------------------------------------------------
# User interface for selecting subregions of a data set.
#
class Region_Size_Panel(PopupPanel):

  name = 'Region bounds'           # Used in feature menu.
  
  def __init__(self, dialog, parent):

    self.dialog = dialog

    PopupPanel.__init__(self, parent)
    
    frame = self.frame

    rl = Tkinter.Label(frame, text = 'Region min max step ')
    rl.grid(row = 0, column = 0, sticky = 'w')

    col = 1
    self.region_bounds = []
    for axis_name in ('x', 'y', 'z'):
      rb = Hybrid.Entry(frame, axis_name, 9)
      rb.frame.grid(row = 0, column = col, sticky = 'w')
      col += 1
      self.region_bounds.append(rb.variable)
      rb.entry.bind('<KeyPress-Return>', self.changed_region_text_cb)
    
    b = self.make_close_button(frame)
    b.grid(row = 0, column = col, sticky = 'e')

    frame.columnconfigure(col, weight = 1)

  # ---------------------------------------------------------------------------
  #
  def use_gui_settings(self, data_region):

    region = self.grid_region()
    from volume import is_empty_region
    if is_empty_region(region):
      return

    ijk_min, ijk_max, ijk_step = region
    data_region.new_region(ijk_min, ijk_max, ijk_step, show = False)

  # ---------------------------------------------------------------------------
  #
  def update_panel_widgets(self, data_region):

    if data_region == None:
      for rb in self.region_bounds:
        rb.set('')
    else:
      self.update_panel_ijk_bounds(*data_region.region)
      
  # ---------------------------------------------------------------------------
  #
  def update_panel_ijk_bounds(self, ijk_min, ijk_max, ijk_step):

    self.set_region_gui_min_max(ijk_min, ijk_max)
    self.set_region_gui_step(ijk_step)
    
  # ---------------------------------------------------------------------------
  # User typed new region bounds in entry field.
  #
  def changed_region_text_cb(self, event):

    dr = active_volume()
    if dr:
      ijk_min, ijk_max, ijk_step = self.grid_region()
      dr.new_region(ijk_min, ijk_max, ijk_step, adjust_step = False)
      
  # ---------------------------------------------------------------------------
  #
  def set_region_gui_min_max(self, ijk_min, ijk_max):

    for a in range(3):
      rb = self.region_bounds[a]
      minmax, step = split_fields(rb.get(), 2)
      rb.set('%d %d %s' % (ijk_min[a], ijk_max[a], step))
      
  # ---------------------------------------------------------------------------
  #
  def set_region_gui_step(self, ijk_step):

    for a in range(3):
      rb = self.region_bounds[a]
      minmax, step = split_fields(rb.get(), 2)
      rb.set('%s %d' % (minmax, ijk_step[a]))
  
  # ---------------------------------------------------------------------------
  #
  def grid_region(self):

    ijk_min = [0,0,0]
    ijk_max = [0,0,0]
    ijk_step = [1,1,1]

    bounds = map(integer_variable_values, self.region_bounds)
    for a in range(3):
      b = bounds[a]
      if len(b) > 0 and b[0] != None: ijk_min[a] = b[0]
      if len(b) > 1 and b[1] != None: ijk_max[a] = b[1]
      if len(b) > 2 and b[2] != None: ijk_step[a] = max(1, b[2])

    return (ijk_min, ijk_max, ijk_step)

# -----------------------------------------------------------------------------
# User interface for selecting subregions of a data set.
#
class Atom_Box_Panel(PopupPanel):

  name = 'Atom box'           # Used in feature menu.
  
  def __init__(self, dialog, parent):

    self.dialog = dialog

    PopupPanel.__init__(self, parent)
    
    frame = self.frame
    frame.columnconfigure(2, weight = 1)

    bb = Tkinter.Button(frame, text = 'Box', command = self.atom_box_cb)
    bb.grid(row = 0, column = 0, sticky = 'w')

    pe = Hybrid.Entry(frame, ' around selected atoms with padding ', 5, '0')
    pe.frame.grid(row = 0, column = 1, sticky = 'w')
    self.box_padding = pe.variable
    pe.entry.bind('<KeyPress-Return>', self.atom_box_cb)
    
    b = self.make_close_button(frame)
    b.grid(row = 0, column = 2, sticky = 'e')

  # ---------------------------------------------------------------------------
  #
  def use_gui_settings(self, data_region):

    pass

  # ---------------------------------------------------------------------------
  #
  def update_panel_widgets(self, data_region):

    pass
    
  # ---------------------------------------------------------------------------
  #
  def atom_box_cb(self, event = None):

    pad = float(self.box_padding.get())
    self.set_region_to_atom_box(pad)
    
  # ---------------------------------------------------------------------------
  #
  def set_region_to_atom_box(self, pad):

    import chimera.selection
    atoms = chimera.selection.currentAtoms()
    if len(atoms) == 0:
      return

    points = map(lambda a: a.xformCoord().data(), atoms)

    dr = active_volume()
    if dr == None:
      return

    xform_to_volume = dr.model_transform()
    if xform_to_volume == None:
      return
    xform_to_volume.invert()

    import volume
    vpoints = volume.transformed_points(points, xform_to_volume)

    from VolumeData import points_ijk_bounds
    ijk_min, ijk_max = points_ijk_bounds(vpoints, pad, dr.data)

    dr.new_region(ijk_min, ijk_max)

# -----------------------------------------------------------------------------
# User interface for selecting subregions of a data set.
#
class Subregion_Panel(PopupPanel):

  name = 'Subregion selection'           # Used in feature menu.
  
  def __init__(self, dialog, parent):

    self.dialog = dialog
    self.subregion_selector = None
    self.last_subregion = (None, None)

    PopupPanel.__init__(self, parent)
    
    frame = self.frame
    frame.columnconfigure(0, weight = 1)
    row = 0

    srf = Tkinter.Frame(frame)
    srf.grid(row = row, column = 0, sticky = 'ew')
    srf.columnconfigure(2, weight = 1)
    row += 1
    
    sr = Hybrid.Checkbutton(srf, 'Select subregions using ', 0)
    sr.button.grid(row = 0, column = 0, sticky = 'w')
    self.selectable_subregions = sr.variable
    sr.callback(self.selectable_subregions_cb)

    srm = Hybrid.Option_Menu(srf, '', *mouse_button_names)
    srm.variable.set('middle')
    srm.frame.grid(row = 0, column = 1, sticky = 'w')
    srm.add_callback(self.subregion_button_cb)
    self.subregion_button = srm.variable

    srl = Tkinter.Label(srf, text = ' mouse button')
    srl.grid(row = 0, column = 2, sticky = 'w')
    
    b = self.make_close_button(srf)
    b.grid(row = 0, column = 2, sticky = 'e')

    cf = Tkinter.Frame(frame)
    cf.grid(row = row, column = 0, sticky = 'w')
    row += 1

    cb = Hybrid.Button_Row(cf, '', (('Crop', self.crop_cb),))
    cb.frame.grid(row = 0, column = 0, sticky = 'nw')
    
    aus = Hybrid.Checkbutton(cf, 'auto', False)
    aus.button.grid(row = 0, column = 1, sticky = 'w')
    self.auto_show_subregion = aus.variable

    zb = Hybrid.Button_Row(cf, '',
                           (('Back', self.back_cb),
                            ('Forward', self.forward_cb),
                            ('Full', self.zoom_full_cb),
                            ))
    zb.frame.grid(row = 0, column = 2, sticky = 'nw')
    self.back_button = zb.buttons[0]
    self.back_button['state'] = 'disabled'
    self.forward_button = zb.buttons[1]
    self.forward_button['state'] = 'disabled'

    rsf = Tkinter.Frame(frame)
    rsf.grid(row = row, column = 0, sticky = 'ew')
    rsf.columnconfigure(2, weight = 1)
    row += 1

    rb = Hybrid.Checkbutton(rsf, 'Rotate selection box,', 0)
    rb.button.grid(row = 0, column = 0, sticky = 'w')
    self.rotate_box = rb.variable
    rb.callback(self.rotate_box_cb)

    vs = Hybrid.Entry(rsf, ' sample at voxel size ', 6)
    vs.frame.grid(row = 0, column = 1, sticky = 'ew')
    self.resample_voxel_size = vs.variable

  # ---------------------------------------------------------------------------
  #
  def use_gui_settings(self, data_region):

    pass
    
  # ---------------------------------------------------------------------------
  #
  def default_settings_changed(self, default_settings, changes):

    if 'auto_show_subregion' in changes:
      self.auto_show_subregion.set(changes['auto_show_subregion'])

  # ---------------------------------------------------------------------------
  #
  def update_panel_widgets(self, data_region):
      
    self.activate_back_forward(data_region)
    if data_region:
      self.resample_voxel_size.set(vector_value_text(data_region.data.step))

  # ---------------------------------------------------------------------------
  #
  def update_panel_ijk_bounds(self, ijk_min, ijk_max, ijk_step):

    self.activate_back_forward(active_volume())

  # ---------------------------------------------------------------------------
  #
  def insert_region_in_queue(self, data_region, ijk_min, ijk_max):

    data_region.region_list.insert_region(ijk_min, ijk_max)
    self.activate_back_forward(data_region)

  # ---------------------------------------------------------------------------
  #
  def activate_back_forward(self, data_region):

    if data_region == None:
      back = 0
      forward = 0
    else:
      from_beginning, from_end = data_region.region_list.where()
      back = (from_beginning > 0)
      forward = (from_end > 0)

    if back:
      self.back_button['state'] = 'normal'
    else:
      self.back_button['state'] = 'disabled'

    if forward:
      self.forward_button['state'] = 'normal'
    else:
      self.forward_button['state'] = 'disabled'
      
  # ---------------------------------------------------------------------------
  #
  def crop_cb(self):

    if self.need_resample():
      self.resample(replace = True)
      return

    ijk_min, ijk_max = self.subregion_box_bounds()
    if ijk_min == None or ijk_max == None:
      self.dialog.message('No subregion selected for cropping')
      return

    v = active_volume()
    if v:
      # Make sure at least one integer plane in each dimension.
      from math import ceil
      ijk_max = [max(ijk_max[a], ceil(ijk_min[a])) for a in (0,1,2)]
      v.new_region(ijk_min, ijk_max)
      
  # ---------------------------------------------------------------------------
  #
  def subregion_box_bounds(self):
    
    ss = self.subregion_selector
    v = active_volume()
    if ss == None or v == None:
      return None, None

    return ss.ijk_box_bounds(v.model_transform(),
                             v.data.ijk_to_xyz_transform)
      
  # ---------------------------------------------------------------------------
  #
  def back_cb(self):

    self.switch_region(-1)
      
  # ---------------------------------------------------------------------------
  #
  def forward_cb(self):

    self.switch_region(1)
      
  # ---------------------------------------------------------------------------
  #
  def switch_region(self, offset):

    dr = active_volume()
    if dr == None:
      return

    ijk_min, ijk_max = dr.region_list.other_region(offset)
    if ijk_min == None or ijk_max == None:
      return

    dr.new_region(ijk_min, ijk_max)
    
  # ---------------------------------------------------------------------------
  #
  def zoom_full_cb(self):

    dr = active_volume()
    if dr == None:
      return

    ijk_min = [0, 0, 0]
    ijk_max = map(lambda n: n-1, dr.data.size)
    dr.new_region(ijk_min, ijk_max)
    
  # ---------------------------------------------------------------------------
  #
  def zoom(self, factor):

    dr = active_volume()
    if dr == None or dr.region == None:
      return

    ijk_min, ijk_max, ijk_step = dr.region
    size = map(lambda a,b: (b - a + 1), ijk_min, ijk_max)
    f = .5 * (factor - 1)
    zoom_ijk_min = map(lambda i,s,f=f: i - f*s, ijk_min, size)
    zoom_ijk_max = map(lambda i,s,f=f: i + f*s, ijk_max, size)

    # If zoomed in to less than one plane, display at least one plane.
    for a in range(3):
      if zoom_ijk_max[a] - zoom_ijk_min[a] < 1:
        mid = .5 * (zoom_ijk_max[a] + zoom_ijk_min[a])
        zoom_ijk_max[a] = mid + 0.5
        zoom_ijk_min[a] = mid - 0.5

    dr.new_region(zoom_ijk_min, zoom_ijk_max)
  
  # ---------------------------------------------------------------------------
  #
  def selectable_subregions_cb(self):

    ss = self.subregion_selector
    if self.selectable_subregions.get():
      if ss == None:
        import selectregion
        self.subregion_selector = selectregion.Select_Volume_Subregion(self.box_changed_cb, save_in_session = False)
      button, modifiers = button_spec(self.subregion_button.get())
      self.subregion_selector.bind_mouse_button(button, modifiers)
    else:
      if ss:
        ss.unbind_mouse_button()
        ss.box_model.delete_box()
        self.last_subregion = (None, None)
      self.rotate_box.set(False)
    
  # ---------------------------------------------------------------------------
  #
  def subregion_button_cb(self):

    if self.selectable_subregions.get() and self.subregion_selector:
      button, modifiers = button_spec(self.subregion_button.get())
      self.subregion_selector.bind_mouse_button(button, modifiers)

  # ---------------------------------------------------------------------------
  #
  def box_changed_cb(self, initial_box):

    if self.auto_show_subregion.get() and not initial_box:
      self.crop_cb()

  # ---------------------------------------------------------------------------
  #
  def rotate_box_cb(self):

    ss = self.subregion_selector
    if ss:
      r = self.rotate_box.get()
      ss.rotate_box(r)

  # ---------------------------------------------------------------------------
  #
  def need_resample(self):

    if self.rotate_box.get():
      return True

    v = active_volume()
    ss = self.subregion_selector
    if v is None or ss is None:
      return False

    pv = getattr(v, 'subregion_of_volume', None)
    if pv and not pv.__destroyed__:
      return True

    m = ss.box_model.model()
    if m is None:
      return False

    same = (m.openState.xform.getCoordFrame() ==
            v.openState.xform.getCoordFrame())
    return not same

  # ---------------------------------------------------------------------------
  #
  def resample(self, replace = False):

    v = active_volume()
    if v is None:
      return

    if (hasattr(v, 'subregion_of_volume')
        and not v.subregion_of_volume.__destroyed__):
      sv = v
      v = v.subregion_of_volume
      if self.last_subregion == (None, None):
        self.last_subregion = (sv, v)

    ss = self.subregion_selector
    if ss is None:
      return

    rvsize = self.resample_voxel_size.get()
    try:
      rstep = [float(f) for f in rvsize.split()]
    except ValueError:
      self.dialog.message('Invalid resample voxel size "%s"' % rvsize)
      return
    
    if len(rstep) == 1:
      rstep *= 3
    if len(rstep) != 3:
      self.dialog.message('Resample voxel size must be 1 or 3 values')
      return

    g = ss.subregion_grid(rstep, v.model_transform(), v.name + ' resampled')
    if g is None:
      self.last_subregion = (None, None)
      return

    lsv, lv = self.last_subregion
    if replace and v is lv and not lsv.__destroyed__:
      sv = lsv
      sv.openState.xform = v.model_transform()
      from volume import replace_data, full_region
      replace_data(sv.data, g)
      sv.add_interpolated_values(v)
      sv.new_region(*full_region(g.size))
      sv.data_changed_cb('coordinates changed')
      sv.show()
    else:
      from VolumeViewer import volume_from_grid_data
      sv = volume_from_grid_data(g, show_data = False)
      sv.openState.xform = v.model_transform()
      if self.rotate_box.get():
        sv.openState.active = False
      sv.add_interpolated_values(v)
      sv.copy_settings_from(v, copy_region = False, copy_xform = False)
      if not replace:
        sv.set_parameters(show_outline_box = True)
      sv.initialize_thresholds()
      self.last_subregion = (sv, v)
      sv.subregion_of_volume = v
      sv.show()
      v.unshow()
    
# -----------------------------------------------------------------------------
# User interface for zones.
#
class Zone_Panel(PopupPanel):

  name = 'Zone'           # Used in feature menu.
  
  def __init__(self, dialog, parent):

    self.dialog = dialog

    PopupPanel.__init__(self, parent)
    
    frame = self.frame
    frame.columnconfigure(0, weight = 1)
    row = 0

    zf = Tkinter.Frame(frame)
    zf.grid(row = row, column = 0, sticky = 'ew')
    zf.columnconfigure(3, weight = 1)
    row += 1

    zb = Tkinter.Button(zf, text = 'Zone', command = self.zone_cb)
    zb.grid(row = 0, column = 0, sticky = 'w')

    zl2 = Tkinter.Label(zf, text = ' near selected atoms. ')
    zl2.grid(row = 0, column = 1, sticky = 'w')

    nzb = Tkinter.Button(zf, text = 'No Zone', command = self.no_zone_cb)
    nzb.grid(row = 0, column = 2, sticky = 'w')

    mb = Tkinter.Button(zf, text = 'Mask', command = self.mask_cb)
    mb.grid(row = 0, column = 3, sticky = 'w')
    
    b = self.make_close_button(zf)
    b.grid(row = 0, column = 4, sticky = 'e')

    rs = Hybrid.Scale(frame, 'Radius ', 0, 30, .1, 2)
    rs.frame.grid(row = row, column = 0, sticky = 'ew')
    row += 1
    rs.callback(self.zone_radius_changed_cb)
    rs.entry.bind('<KeyPress-Return>', self.zone_radius_changed_cb)
    self.zone_radius = rs

  # ---------------------------------------------------------------------------
  #
  def use_gui_settings(self, data_region):

    pass
  
  # ---------------------------------------------------------------------------
  #
  def update_panel_widgets(self, data_region):

    if data_region:
      self.set_zone_radius_slider_range(data_region)
    
  # ---------------------------------------------------------------------------
  #
  def zone_cb(self, event = None, mask = False):

    surface = self.zone_surface()
    if surface == None:
      self.dialog.message('No surface shown for active volume')
      return

    radius = self.zone_radius_from_gui()
    if radius == None:
      self.dialog.message('No zone radius specified')
      return

    from chimera import selection
    atoms = selection.currentAtoms()
    bonds = selection.currentBonds()

    from SurfaceZone import path_points, surface_zone
    points = path_points(atoms, bonds, surface.openState.xform.inverse())
    if len(points) > 0:
      if mask:
        v = active_volume()
        import VolumeFilter as VF
        zv = VF.zone_volume(v, points, radius)
      else:
        self.resize_region_for_zone(points, radius, initial_resize = True)
        surface_zone(surface, points, radius, auto_update = True)
    else:
      self.dialog.message('No atoms are selected for zone')
    
  # ---------------------------------------------------------------------------
  #
  def mask_cb(self, event = None):
      
    self.zone_cb(mask = True)

  # ---------------------------------------------------------------------------
  #
  def no_zone_cb(self, event = None):

    surface = self.zone_surface()
    if surface:
      import SurfaceZone
      SurfaceZone.no_surface_zone(surface)
      self.dialog.subregion_panel.zoom_full_cb()

  # ---------------------------------------------------------------------------
  #
  def zone_radius_changed_cb(self, event = None):

    surface = self.zone_surface()
    if surface == None:
        return

    import SurfaceZone
    if SurfaceZone.showing_zone(surface):
      radius = self.zone_radius_from_gui()
      if radius != None:
        points, old_radius = SurfaceZone.zone_points_and_distance(surface)
        self.resize_region_for_zone(points, radius)
        SurfaceZone.surface_zone(surface, points, radius, auto_update = True)
      
  # ---------------------------------------------------------------------------
  #
  def zone_radius_from_gui(self):

    radius = self.zone_radius.value()
    if radius == None:
      self.dialog.message('Radius is set to a non-numeric value')
      return None
    else:
      self.dialog.message('')
    return radius
      
  # ---------------------------------------------------------------------------
  #
  def zone_surface(self):

    data_region = active_volume()
    if data_region == None:
      return None

    surface = data_region.surface_model()
    return surface

  # ---------------------------------------------------------------------------
  # Adjust volume region to include a zone.  If current volume region is
  # much bigger than that needed for the zone, then shrink it.  The purpose
  # of this resizing is to keep the region small so that recontouring is fast,
  # but not resize on every new zone radius.  Resizing on every new zone
  # radius requires recontouring and redisplaying the volume histogram which
  # slows down zone radius updates.
  #
  def resize_region_for_zone(self, points, radius, initial_resize = False):

    dr = active_volume()
    if dr is None:
      return

    from volume import resize_region_for_zone
    new_ijk_min, new_ijk_max = resize_region_for_zone(dr, points,
                                                      radius, initial_resize)
    if not new_ijk_min is None:
      dr.new_region(new_ijk_min, new_ijk_max, save_in_region_queue = False)

  # ---------------------------------------------------------------------------
  # Use diagonal length of bounding box of full data set.
  #
  def set_zone_radius_slider_range(self, data_region):

    import volume
    r = volume.maximum_data_diagonal_length(data_region.data)

    step = r / 1000.0
    if step > 0:
      step = smaller_power_of_ten(step)

    # A step of 0 is supposed to make Tk scale have not discretization.
    # But in Tk 8.4 it appears to discretize giving only integer values for
    # a scale range 0 to 101.

    self.zone_radius.set_range(0, r, step)
  
# -----------------------------------------------------------------------------
#
def smaller_power_of_ten(x):

  from math import pow, floor, log10
  y = pow(10, floor(log10(x)))
  return y

# -----------------------------------------------------------------------------
# User interface for setting general data display and management options.
#
class Display_Options_Panel(PopupPanel):

  name = 'Data display options'           # Used in feature menu.
  
  def __init__(self, dialog, parent):

    self.dialog = dialog

    PopupPanel.__init__(self, parent)
    
    frame = self.frame
    frame.columnconfigure(0, weight = 1)
    
    row = 0

    obf = Tkinter.Frame(frame)
    obf.grid(row = row, column = 0, sticky = 'new')
    obf.columnconfigure(2, weight = 1)
    row += 1

    ob = Hybrid.Checkbutton(obf, 'Show outline box using color ', 0)
    ob.button.grid(row = 0, column = 0, sticky = 'w')
    self.show_outline_box = ob.variable
    self.show_outline_box.add_callback(dialog.redisplay_needed_cb)

    from CGLtk.color import ColorWell
    cb = lambda rgba, d=dialog: d.redisplay_needed_cb()
    obc = ColorWell.ColorWell(obf, width = 25, height = 25, callback = cb)
    obc.grid(row = 0, column = 1, sticky = 'w')
    self.outline_box_color = obc

    lw = Hybrid.Entry(obf, ' linewidth ', 3, '1')
    lw.frame.grid(row = 0, column = 2, sticky = 'w')
    self.outline_width = lw.variable
    lw.entry.bind('<KeyPress-Return>', dialog.redisplay_needed_cb)
    
    b = self.make_close_button(obf)
    b.grid(row = 0, column = 2, sticky = 'e')

    mh = Hybrid.Entry(frame, 'Maximum number of histograms shown ', 4, '3')
    mh.frame.grid(row = row, column = 0, sticky = 'w')
    row += 1
    self.max_histograms = mh.variable
    mh.entry.bind('<KeyPress-Return>',
                  dialog.thresholds_panel.max_histograms_cb)

    icf = Tkinter.Frame(frame)
    icf.grid(row = row, column = 0, sticky = 'new')
    icf.columnconfigure(11, weight = 1)
    row += 1

    icb = Hybrid.Checkbutton(icf, 'Initial colors ', True)
    icb.button.grid(row = 0, column = 0, sticky = 'w')
    self.use_initial_colors = icb.variable
    self.use_initial_colors.add_callback(self.update_global_defaults)
    
    self.initial_colors = []
    for c in range(10):
      from CGLtk.color import ColorWell
      ic = ColorWell.ColorWell(icf, width = 20, height = 20,
                               callback = self.update_global_defaults)
      ic.grid(row = 0, column = c+1, sticky = 'w')
      self.initial_colors.append(ic)

    iu = Hybrid.Checkbutton(frame, 'Update display automatically', True)
    iu.button.grid(row = row, column = 0, sticky = 'nw')
    row += 1
    self.immediate_update = iu.variable
    self.immediate_update.add_callback(self.immediate_update_cb)

    sop = Hybrid.Checkbutton_Entries(frame, False,
                                     'Show data when opened if smaller than',
                                     (4, ''),
                                     ' Mvoxels')
    sop.frame.grid(row = row, column = 0, sticky = 'nw')
    row += 1
    self.show_on_open, self.voxel_limit_for_open = sop.variables
    self.show_on_open.add_callback(self.update_global_defaults)
    sop.entries[0].bind('<KeyPress-Return>', self.update_global_defaults)


    spl = Hybrid.Checkbutton_Entries(frame, True,
                                     'Show plane when data larger than',
                                     (4, ''),
                                     ' Mvoxels')
    spl.frame.grid(row = row, column = 0, sticky = 'nw')
    row += 1
    self.show_plane, self.voxel_limit_for_plane = spl.variables
    self.show_plane.add_callback(self.update_global_defaults)
    sop.entries[0].bind('<KeyPress-Return>', self.update_global_defaults)
    
    ssb = Hybrid.Checkbutton_Entries(frame, True,
                                     'Adjust step to show at most',
                                     (4, '1'),
                                     ' Mvoxels')
    ssb.frame.grid(row = row, column = 0, sticky = 'nw')
    row += 1
    self.limit_voxel_count, self.voxel_limit = ssb.variables
    self.limit_voxel_count.add_callback(dialog.redisplay_needed_cb)
    ssb.entries[0].bind('<KeyPress-Return>', dialog.redisplay_cb)

    vc = Tkinter.Frame(frame)
    vc.grid(row = row, column = 0, sticky = 'w')
    row += 1

    from VolumeData import data_cache
    csize = data_cache.size / (2 ** 20)
    cs = Hybrid.Entry(vc, 'Data cache size (Mb)', 4, csize)
    cs.frame.grid(row = 0, column = 0, sticky = 'w')
    self.data_cache_size = cs.variable
    cs.entry.bind('<KeyPress-Return>', self.cache_size_cb)

    cu = Tkinter.Button(vc, text = 'Current use', command = self.cache_use_cb)
    cu.grid(row = 0, column = 1, sticky = 'w')
    
    ac = Hybrid.Checkbutton(frame,
                            'Zoom and center camera when region changes', 0)
    ac.button.grid(row = row, column = 0, sticky = 'w')
    row += 1
    self.adjust_camera = ac.variable

  # ---------------------------------------------------------------------------
  #
  def update_global_defaults(self, event = None):

    from volume import default_settings as ds
    ds.set_defaults_from_gui(self.dialog, global_settings = True,
                             data_settings = False, panel_settings = False)

  # ---------------------------------------------------------------------------
  #
  def immediate_update_cb(self):

    d = self.dialog
    b = d.update_button
    if self.immediate_update.get():
      b.pack_forget()                              # Unshow update button
    else:
      b.pack(d.update_button_pack_settings)        # Show update button
    d.redisplay_needed_cb()

  # ---------------------------------------------------------------------------
  #
  def cache_size_cb(self, event = None):

    size_mb = float_variable_value(self.data_cache_size, None)
    if size_mb:
      from VolumeData import data_cache
      data_cache.resize(size_mb * (2**20))
        
  # ---------------------------------------------------------------------------
  #
  def cache_use_cb(self):

    from VolumeData import memoryuse
    memoryuse.show_memory_use_dialog()
    
  # ---------------------------------------------------------------------------
  #
  def default_settings_changed(self, default_settings, changes):

    self.set_gui_state(changes)
    
  # ---------------------------------------------------------------------------
  #
  def set_gui_state(self, settings):

    for b in ('use_initial_colors', 'immediate_update', 'show_on_open',
              'show_plane', 'adjust_camera'):
      if b in settings:
        var = getattr(self, b)
        var.set(settings[b], invoke_callbacks = False)

    from defaultsettings import number_string
    for v in ('max_histograms', 'voxel_limit_for_open',
              'voxel_limit_for_plane', 'data_cache_size'):
      if v in settings:
        var = getattr(self, v)
        var.set(number_string(settings[v]), invoke_callbacks = False)

    if 'data_cache_size' in settings:
      self.cache_size_cb()

    if 'initial_colors' in settings:
      icolors = settings['initial_colors']
      for c in range(10):
        self.initial_colors[c].showColor(icolors[c], doCallback = False)
    
  # ---------------------------------------------------------------------------
  #
  def get_gui_state(self, settings):

    for b in ('use_initial_colors', 'immediate_update', 'show_on_open',
              'show_plane', 'adjust_camera'):
      var = getattr(self, b)
      settings[b] = var.get()

    from defaultsettings import float_value
    from volume import default_settings
    for v in ('max_histograms', 'voxel_limit_for_open',
              'voxel_limit_for_plane', 'data_cache_size'):
      var = getattr(self, v)
      settings[v] = float_value(var.get(), default_settings[v])

    colors = tuple([c.rgba for c in self.initial_colors])
    settings['initial_colors'] = colors
        
  # ---------------------------------------------------------------------------
  #
  def ijk_step_for_voxel_limit(self, ijk_min, ijk_max, ijk_step):
    
    mvoxels = float_variable_value(self.voxel_limit)
    import volume
    step = volume.ijk_step_for_voxel_limit(ijk_min, ijk_max, ijk_step,
                                           self.limit_voxel_count.get(),
                                           mvoxels)
    return step

  # ---------------------------------------------------------------------------
  #
  def update_panel_widgets(self, data_region):

    if data_region == None:
      return
    
    ro = data_region.rendering_options
    if ro:
      self.set_gui_from_rendering_options(ro)

  # ---------------------------------------------------------------------------
  #
  def use_gui_settings(self, data_region):

    self.rendering_options_from_gui(data_region.rendering_options)

  # ---------------------------------------------------------------------------
  #
  def set_gui_from_rendering_options(self, ro):

    self.show_outline_box.set(ro.show_outline_box, invoke_callbacks = False)
    self.outline_box_color.showColor(ro.outline_box_rgb, doCallback = False)
    self.outline_width.set('%.3g' % ro.outline_box_linewidth,
                           invoke_callbacks = False)

    self.set_gui_voxel_limit(ro)

  # ---------------------------------------------------------------------------
  #
  def set_gui_voxel_limit(self, ro):

    self.limit_voxel_count.set(ro.limit_voxel_count, invoke_callbacks = False)
    self.voxel_limit.set('%.3g' % ro.voxel_limit, invoke_callbacks = False)

  # ---------------------------------------------------------------------------
  #
  def rendering_options_from_gui(self, ro):
    
    ro.show_outline_box = self.show_outline_box.get()
    ro.outline_box_rgb = self.outline_box_color.rgb
    ro.outline_box_linewidth = float_variable_value(self.outline_width, 1)
    ro.limit_voxel_count = self.limit_voxel_count.get()
    ro.voxel_limit = float_variable_value(self.voxel_limit, 1)

# -----------------------------------------------------------------------------
# User interface for setting solid rendering options.
#
class Solid_Options_Panel(PopupPanel):

  name = 'Solid rendering options'           # Used in feature menu.
  
  def __init__(self, dialog, parent):

    self.dialog = dialog

    PopupPanel.__init__(self, parent)
    
    frame = self.frame
    frame.columnconfigure(0, weight = 1)

    row = 0

    cmf = Tkinter.Frame(frame)
    cmf.grid(row = row, column = 0, sticky = 'new')
    cmf.columnconfigure(2, weight=1)
    row += 1
    
    b = self.make_close_button(cmf)
    b.grid(row = 0, column = 2, sticky = 'e')

    self.color_mode_descriptions = (
      ('auto', 'auto'),
      ('opaque', 'opaque'),
      ('rgba', 'multi-color transparent'),
      ('rgb', 'multi-color opaque'),
      ('la', 'single-color transparent'),
      ('l', 'single-color opaque'))
    descrip = [d for m,d in self.color_mode_descriptions]
    cm = Hybrid.Option_Menu(cmf, 'Color mode:', *descrip)
    cm.button.configure(indicatoron = False)
    cm.frame.grid(row = 0, column = 0, sticky = 'w')
    self.color_mode = cm.variable
    cm.add_callback(dialog.redisplay_needed_cb)

    cb = Hybrid.Option_Menu(cmf, '', '4 bits', '8 bits', '12 bits', '16 bits')
    cb.button.configure(indicatoron = False)
    cb.frame.grid(row = 0, column = 1, sticky = 'w')
    self.color_mode_bits = cb.variable
    cb.add_callback(dialog.redisplay_needed_cb)

    pmodes = (('auto','auto'),
              ('2d-xyz','x, y or z planes'),
              ('2d-x','x planes'),
              ('2d-y','y planes'),
              ('2d-z','z planes'),
              ('3d','perpendicular to view'))
    pm = Hybrid.Option_Menu(frame, 'Projection mode', *[n for m,n in pmodes])
    pm.button.configure(indicatoron = False)
    pm.frame.grid(row = row, column = 0, sticky = 'w')
    row += 1
    self.projection_mode = pm.variable
    pm.add_callback(dialog.redisplay_needed_cb)
    self.proj_mode_name = dict(pmodes)
    self.proj_mode_from_name = dict([(n,m) for m,n in pmodes])
    
    mipd = 'Maximum intensity projection'
    import _volume
    if not _volume.maximum_intensity_projection_supported():
      mipd = mipd + ' (not available)'
    mp = Hybrid.Checkbutton(frame, mipd, 0)
    mp.button.grid(row = row, column = 0, sticky = 'w')
    row += 1
    self.maximum_intensity_projection = mp.variable
    self.maximum_intensity_projection.add_callback(dialog.redisplay_needed_cb)

    dt = Hybrid.Checkbutton(frame, 'Dim transparent voxels', False)
    dt.button.grid(row = row, column = 0, sticky = 'nw')
    row += 1
    self.dim_transparent_voxels = dt.variable
    self.dim_transparent_voxels.add_callback(dialog.redisplay_needed_cb)
    
    bt = Hybrid.Checkbutton(frame, 'Solid brightness correction', 0)
    bt.button.grid(row = row, column = 0, sticky = 'nw')
    row += 1
    self.bt_correction = bt.variable
    self.bt_correction.add_callback(dialog.redisplay_needed_cb)
    
    mt = Hybrid.Checkbutton(frame, 'Minimize texture memory use', 0)
    mt.button.grid(row = row, column = 0, sticky = 'nw')
    row += 1
    self.minimal_texture_memory = mt.variable
    self.minimal_texture_memory.add_callback(dialog.redisplay_needed_cb)
    
    vli = Hybrid.Checkbutton(frame, 'Solid linear interpolation', 0)
    vli.button.grid(row = row, column = 0, sticky = 'nw')
    row += 1
    self.linear_interpolation = vli.variable
    self.linear_interpolation.add_callback(dialog.redisplay_needed_cb)

  # ---------------------------------------------------------------------------
  #
  def update_panel_widgets(self, data_region):

    if data_region == None:
      return
    
    ro = data_region.rendering_options
    if ro:
      self.set_gui_from_rendering_options(ro)

  # ---------------------------------------------------------------------------
  #
  def use_gui_settings(self, data_region):

    self.rendering_options_from_gui(data_region.rendering_options)

  # ---------------------------------------------------------------------------
  #
  def set_gui_from_rendering_options(self, ro):

    self.maximum_intensity_projection.set(ro.maximum_intensity_projection,
                                          invoke_callbacks = False)
    m,b = self.color_mode_from_name(ro.color_mode)
    self.color_mode.set(m, invoke_callbacks = False)
    self.color_mode_bits.set(b, invoke_callbacks = False)
    self.projection_mode.set(self.proj_mode_name[ro.projection_mode],
                             invoke_callbacks = False)
    self.dim_transparent_voxels.set(ro.dim_transparent_voxels,
                                    invoke_callbacks = False)
    self.bt_correction.set(ro.bt_correction, invoke_callbacks = False)
    self.minimal_texture_memory.set(ro.minimal_texture_memory,
                                    invoke_callbacks = False)
    self.linear_interpolation.set(ro.linear_interpolation,
                                  invoke_callbacks = False)

  # ---------------------------------------------------------------------------
  #
  def rendering_options_from_gui(self, ro):
    
    ro.color_mode = self.color_mode_name()
    ro.projection_mode = self.proj_mode_from_name[self.projection_mode.get()]
    ro.maximum_intensity_projection = self.maximum_intensity_projection.get()
    ro.dim_transparent_voxels = self.dim_transparent_voxels.get()
    ro.bt_correction = self.bt_correction.get()
    ro.minimal_texture_memory = self.minimal_texture_memory.get()
    ro.linear_interpolation = self.linear_interpolation.get()

  # ---------------------------------------------------------------------------
  #
  def color_mode_name(self):

    cmode = self.color_mode.get()
    mode = [m for m,d in self.color_mode_descriptions if d == cmode][0]
    mname = mode + self.color_mode_bits.get()[:-5] # strip off ' bits' text
    return mname

  # ---------------------------------------------------------------------------
  #
  def color_mode_from_name(self, mname):

    for prefix, descrip in self.color_mode_descriptions:
      if mname.startswith(prefix):
        m = descrip
        break
    b = {'4':'4 bits', '8':'8 bits', '2':'12 bits', '6':'16 bits'}[mname[-1]]
    return m,b

# -----------------------------------------------------------------------------
# User interface for setting surface and mesh rendering options.
#
class Surface_Options_Panel(PopupPanel):

  name = 'Surface and Mesh options'           # Used in feature menu.
  
  def __init__(self, dialog, parent):

    self.dialog = dialog

    PopupPanel.__init__(self, parent)
    
    frame = self.frame
    frame.columnconfigure(0, weight = 1)
    
    row = 0

    smf = Tkinter.Frame(frame)
    smf.grid(row = row, column = 0, sticky = 'new')
    smf.columnconfigure(4, weight = 1)
    row += 1
    
    ssm = Hybrid.Checkbutton_Entries(smf, False,
                                     'Surface smoothing iterations', (2, ''),
                                     ' factor', (4,''))
    ssm.frame.grid(row = 0, column = 0, sticky = 'nw')
    self.surface_smoothing, self.smoothing_iterations, self.smoothing_factor = ssm.variables
    self.surface_smoothing.add_callback(dialog.redisplay_needed_cb)
    for e in ssm.entries:
      e.bind('<KeyPress-Return>', dialog.redisplay_cb)
    
    b = self.make_close_button(smf)
    b.grid(row = 0, column = 4, sticky = 'e')
    
    sd = Hybrid.Checkbutton_Entries(frame, False,
                                    'Subdivide surface',
                                    (2, '1'),
                                    ' times')
    sd.frame.grid(row = row, column = 0, sticky = 'nw')
    row += 1
    self.subdivide_surface, self.subdivision_levels = sd.variables
    self.subdivide_surface.add_callback(dialog.redisplay_needed_cb)
    sd.entries[0].bind('<KeyPress-Return>', dialog.redisplay_cb)
    
    sl = Hybrid.Checkbutton(frame, 'Smooth mesh lines', 0)
    sl.button.grid(row = row, column = 0, sticky = 'nw')
    row += 1
    self.smooth_lines = sl.variable
    self.smooth_lines.add_callback(dialog.redisplay_needed_cb)
    
    sm = Hybrid.Checkbutton(frame, 'Square mesh', False)
    sm.button.grid(row = row, column = 0, sticky = 'nw')
    row += 1
    self.square_mesh = sm.variable
    self.square_mesh.add_callback(dialog.redisplay_needed_cb)

    ltf = Tkinter.Frame(frame)
    ltf.grid(row = row, column = 0, sticky = 'nw')
    row += 1

    lt = Hybrid.Entry(ltf, 'Mesh line thickness', 3, suffix = 'pixels')
    lt.frame.grid(row = 0, column = 0, sticky = 'w')
    lt.entry.bind('<KeyPress-Return>', dialog.redisplay_cb)
    self.line_thickness = lt.variable
    
    ds = Hybrid.Checkbutton(frame, 'Dim transparent surface/mesh', 0)
    ds.button.grid(row = row, column = 0, sticky = 'nw')
    row += 1
    self.dim_transparency = ds.variable
    self.dim_transparency.add_callback(dialog.redisplay_needed_cb)
    
    ml = Hybrid.Checkbutton(frame, 'Mesh lighting', 1)
    ml.button.grid(row = row, column = 0, sticky = 'nw')
    row += 1
    self.mesh_lighting = ml.variable
    self.mesh_lighting.add_callback(dialog.redisplay_needed_cb)
    
    l2 = Hybrid.Checkbutton(frame, 'Two-sided surface lighting', 1)
    l2.button.grid(row = row, column = 0, sticky = 'nw')
    row += 1
    self.two_sided_lighting = l2.variable
    self.two_sided_lighting.add_callback(dialog.redisplay_needed_cb)
    
    fn = Hybrid.Checkbutton(frame, 'Light flip side for thresholds < 0', 1)
    fn.button.grid(row = row, column = 0, sticky = 'nw')
    row += 1
    self.flip_normals = fn.variable
    self.flip_normals.add_callback(dialog.redisplay_needed_cb)
    
    cp = Hybrid.Checkbutton(frame, 'Cap high values at box faces', True)
    cp.button.grid(row = row, column = 0, sticky = 'nw')
    row += 1
    self.cap_faces = cp.variable
    self.cap_faces.add_callback(dialog.redisplay_needed_cb)

  # ---------------------------------------------------------------------------
  #
  def update_panel_widgets(self, data_region):

    if data_region == None:
      return
    
    ro = data_region.rendering_options
    if ro:
      self.set_gui_from_rendering_options(ro)

  # ---------------------------------------------------------------------------
  #
  def use_gui_settings(self, data_region):

    self.rendering_options_from_gui(data_region.rendering_options)

  # ---------------------------------------------------------------------------
  #
  def set_gui_from_rendering_options(self, ro):

    self.dim_transparency.set(ro.dim_transparency, invoke_callbacks = 0)
    self.line_thickness.set('%.3g' % ro.line_thickness, invoke_callbacks = 0)
    self.smooth_lines.set(ro.smooth_lines, invoke_callbacks = 0)
    self.mesh_lighting.set(ro.mesh_lighting, invoke_callbacks = 0)
    self.two_sided_lighting.set(ro.two_sided_lighting, invoke_callbacks = 0)
    self.flip_normals.set(ro.flip_normals, invoke_callbacks = 0)
    self.subdivide_surface.set(ro.subdivide_surface, invoke_callbacks = 0)
    self.subdivision_levels.set('%d' % ro.subdivision_levels,
                                invoke_callbacks = 0)
    self.surface_smoothing.set(ro.surface_smoothing, invoke_callbacks = 0)
    self.smoothing_iterations.set('%d' % ro.smoothing_iterations,
                                  invoke_callbacks = 0)
    self.smoothing_factor.set('%.3g' % ro.smoothing_factor,
                              invoke_callbacks = 0)
    self.square_mesh.set(ro.square_mesh, invoke_callbacks = 0)
    self.cap_faces.set(ro.cap_faces, invoke_callbacks = False)

  # ---------------------------------------------------------------------------
  #
  def rendering_options_from_gui(self, ro):

    ro.dim_transparency = self.dim_transparency.get()
    lt = float_variable_value(self.line_thickness, 1)
    if lt <= 0:
      lt = 1
    ro.line_thickness = lt
    ro.smooth_lines = self.smooth_lines.get()
    ro.mesh_lighting = self.mesh_lighting.get()
    ro.two_sided_lighting = self.two_sided_lighting.get()
    ro.flip_normals = self.flip_normals.get()
    ro.subdivide_surface = self.subdivide_surface.get()
    sl = integer_variable_value(self.subdivision_levels, 1)
    if sl < 0:
      sl = 0
    ro.subdivision_levels = sl
    ro.surface_smoothing = self.surface_smoothing.get()
    si = integer_variable_value(self.smoothing_iterations, 2)
    if si < 0:
      si = 0
    ro.smoothing_iterations = si
    sf = float_variable_value(self.smoothing_factor, .3)
    if sf < 0: sf = 0
    elif sf > 1: sf = 1
    ro.smoothing_factor = sf
    ro.square_mesh = self.square_mesh.get()
    ro.cap_faces = self.cap_faces.get()

# -----------------------------------------------------------------------------
#
nbfont = None
def non_bold_font(frame):

  global nbfont
  if nbfont == None:
    e = Tkinter.Entry(frame)
    nbfont = e['font']
    e.destroy()
  return nbfont
  
# -----------------------------------------------------------------------------
#
def place_in_grid(widget, place):

  if place:
    widget.grid()
  else:
    widget.grid_remove()
      
# ---------------------------------------------------------------------------
#
mouse_button_names = ('left', 'middle', 'right',
                      'ctrl left', 'ctrl middle', 'ctrl right')
def button_spec(bname):

  name_to_bspec = {'left':('1', []), 'ctrl left':('1', ['Ctrl']),
                   'middle':('2', []), 'ctrl middle':('2', ['Ctrl']),
                   'right':('3', []), 'ctrl right':('3', ['Ctrl'])}
  bspec = name_to_bspec[bname]
  return bspec

# -----------------------------------------------------------------------------
#
def split_fields(s, nfields):

  fields = s.split()
  leading = ' '.join(fields[:nfields])
  trailing = ' '.join(fields[nfields:])
  return leading, trailing

# -----------------------------------------------------------------------------
#
def integer_variable_value(v, default = None):

  try:
    return int(v.get())
  except:
    return default
  
# -----------------------------------------------------------------------------
#
def integer_variable_values(v, default = None):

  fields = v.get().split(' ')
  values = []
  for field in fields:
    try:
      value = int(field)
    except:
      value = default
    values.append(value)
  return values
    
# -----------------------------------------------------------------------------
#
def float_variable_value(v, default = None):

  return string_to_float(v.get(), default)
    
# -----------------------------------------------------------------------------
#
def string_to_float(v, default = None):

  try:
    return float(v)
  except:
    return default
    
# -----------------------------------------------------------------------------
# Format a number using %g but do not use scientific notation for large
# values if the number can be represented more compactly without it.
#
def float_format(value, precision):

  if value == None:
    return ''
  
  import math

  if (abs(value) >= math.pow(10.0, precision) and
      abs(value) < math.pow(10.0, precision + 4)):
    format = '%.0f'
  else:
    format = '%%.%dg' % precision

  if value == 0:
    value = 0           # Avoid including sign bit for -0.0.

  text = format % value

  return text
    
# -----------------------------------------------------------------------------
#
def saturate_rgba(rgba):

  mc = max(rgba[:3])
  if mc > 0:
    s = rgba[0]/mc, rgba[1]/mc, rgba[2]/mc, rgba[3]
  else:
    s = rgba
  return s

# -----------------------------------------------------------------------------
#
def show_volume_file_browser(dialog_title, volumes_cb = None,
                             show_data = False, show_volume_dialog = False):

  def grids_cb(grids):
    from volume import volume_from_grid_data
    vlist = [volume_from_grid_data(g, show_data = show_data,
                                   show_dialog = show_volume_dialog)
             for g in grids]
    if volumes_cb:
      volumes_cb(vlist)

  from VolumeData import show_grid_file_browser
  show_grid_file_browser(dialog_title, grids_cb)

# -----------------------------------------------------------------------------
#
def subregion_selection_bounds():

  d = volume_dialog()
  if d is None:
    return None, None
  ijk_min, ijk_max = d.subregion_panel.subregion_box_bounds()
  return ijk_min, ijk_max

# -----------------------------------------------------------------------------
#
def add_volume_opened_callback(session, volume_opened_cb):
    def models_opened(name, models, cb = volume_opened_cb):
        from chimerax.core.map import Volume
        vlist = [m for m in models if isinstance(m, Volume)]
        if vlist:
            cb(vlist)
    from chimerax.core.models import ADD_MODELS
    h = session.triggers.add_handler(ADD_MODELS, models_opened)
    return h

# -----------------------------------------------------------------------------
#
def add_volume_closed_callback(session, volume_closed_cb):
    def models_closed(name, models, cb = volume_closed_cb):
        from chimerax.core.map import Volume
        vlist = [m for m in models if isinstance(m, Volume)]
        if vlist:
            cb(vlist)
    from chimerax.core.models import REMOVE_MODELS
    h = session.triggers.add_handler(REMOVE_MODELS, models_closed)
    return h

# -----------------------------------------------------------------------------
#
def volume_list(session):
    from chimerax.core.map import Volume
    return session.models.list(type = Volume)
    
# -----------------------------------------------------------------------------
#
def active_volume(session):
    vv = volume_dialog(session)
    v = vv.active_volume if vv else None
    return v

# -----------------------------------------------------------------------------
#
def set_active_volume(session, v):
    vv = volume_dialog(session, create = True)
    vv.display_volume_info(v)
    
# -----------------------------------------------------------------------------
#
def volume_dialog(session, create=False):
    vv = getattr(session, '_volume_viewer', None)
    if vv is None and create:
        bundle_info = session.toolshed.find_bundle('volume_viewer')
        session._volume_viewer = vv = VolumeViewer(session, bundle_info)
    return vv

# -----------------------------------------------------------------------------
#
def show_volume_dialog(session):
    from chimerax.core import window_sys
    if window_sys == "wx":
        return None

    vv = volume_dialog(session, create = True)
    vv.show()
    return vv
