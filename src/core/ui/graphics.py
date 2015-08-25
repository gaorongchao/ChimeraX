# vi: set expandtab ts=4 sw=4:

import wx

class GraphicsWindow(wx.Panel):
    """
    The graphics window that displays the three-dimensional models.
    """

    def __init__(self, parent, ui):
        wx.Panel.__init__(self, parent,
            style=wx.TAB_TRAVERSAL | wx.NO_BORDER | wx.WANTS_CHARS)
        self.timer = None
        self.view = ui.session.main_view
        self.opengl_canvas = OpenGLCanvas(self, self.view, ui)
        from wx.glcanvas import GLContext
        oc = self.opengl_context = GLContext(self.opengl_canvas)
        oc.make_current = self.make_context_current
        oc.swap_buffers = self.swap_buffers
        self.view.initialize_context(oc)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.opengl_canvas, 1, wx.EXPAND)
        self.SetSizerAndFit(sizer)

        self.redraw_interval = 16  # milliseconds
        # perhaps redraw interval should be 10 to reduce
        # frame drops at 60 frames/sec

        from .mousemodes import MouseModes
        self.mouse_modes = MouseModes(self, ui.session)

    def set_redraw_interval(self, msec):
        self.redraw_interval = msec  # milliseconds
        t = self.timer
        if t is not None:
            t.Start(self.redraw_interval)

    def make_context_current(self):
        # creates context if needed
        if self.timer is None:
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self._redraw_timer_callback, self.timer)
            self.timer.Start(self.redraw_interval)
        self.opengl_canvas.SetCurrent(self.opengl_context)

    def swap_buffers(self):
        self.opengl_canvas.SwapBuffers()

    def _redraw_timer_callback(self, event):
        if not self.view.draw_new_frame():
            self.mouse_modes.mouse_pause_tracking()


from wx import glcanvas


class OpenGLCanvas(glcanvas.GLCanvas):

    def __init__(self, parent, view, ui=None, size=None):
        self.view = view
        attribs = [glcanvas.WX_GL_RGBA, glcanvas.WX_GL_DOUBLEBUFFER]
        from ..core_settings import settings
        ppi = max(wx.GetDisplayPPI())
        if ppi < settings.multisample_threshold:
            # TODO: how to pick number of samples
            attribs += [glcanvas.WX_GL_SAMPLE_BUFFERS, 1,
                        glcanvas.WX_GL_SAMPLES, 4]
        import sys
        if sys.platform.startswith('darwin'):
            attribs += [
                glcanvas.WX_GL_OPENGL_PROFILE,
                glcanvas.WX_GL_OPENGL_PROFILE_3_2CORE
            ]
        gl_supported = glcanvas.GLCanvas.IsDisplaySupported
        if not gl_supported(attribs + [0]):
            raise AssertionError("Required OpenGL capabilities, RGBA and/or"
                " double buffering and/or OpenGL 3, not supported")
        for depth in range(32, 0, -8):
            test_attribs = attribs + [glcanvas.WX_GL_DEPTH_SIZE, depth]
            if gl_supported(test_attribs + [0]):
                attribs = test_attribs
                # TODO: log this
                print("Using {}-bit OpenGL depth buffer".format(depth))
                break
        else:
            raise AssertionError("Required OpenGL depth buffer capability"
                " not supported")
        test_attribs = attribs + [glcanvas.WX_GL_STEREO]
        if gl_supported(test_attribs + [0]):
            # TODO: keep track of fact that 3D stereo is available, but
            # don't use it
            pass
        else:
            print("Stereo mode is not supported by OpenGL driver")
        ckw = {} if size is None else {'size': size}
        glcanvas.GLCanvas.__init__(self, parent, -1, attribList=attribs + [0],
                                   style=wx.WANTS_CHARS, **ckw)

        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        if ui:
            self.Bind(wx.EVT_CHAR, ui.forward_keystroke)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_paint(self, event):
        # self.SetCurrent(view.opengl_context())
        self.view.draw()

    def on_size(self, event):
        wx.CallAfter(self.set_viewport)
        event.Skip()

    def set_viewport(self):
        self.view.resize(*self.GetClientSize())


class OculusGraphicsWindow(wx.Frame):
    """
    The graphics window for using Oculus Rift goggles.
    """

    def __init__(self, view, parent=None):

        wx.Frame.__init__(self, parent, title="Oculus Rift")

        class View:

            def draw(self):
                pass

            def resize(self, *args):
                pass
        self.opengl_canvas = OpenGLCanvas(self, View())

        from wx.glcanvas import GLContext
        oc = self.opengl_context = GLContext(self.opengl_canvas, view._opengl_context)
        oc.make_current = self.make_context_current
        oc.swap_buffers = self.swap_buffers
        self.opengl_context = oc
        self.primary_opengl_context = view._opengl_context

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.opengl_canvas, 1, wx.EXPAND)
        self.SetSizerAndFit(sizer)

        self.Show(True)

    def make_context_current(self):
        self.opengl_canvas.SetCurrent(self.opengl_context)

    def swap_buffers(self):
        self.opengl_canvas.SwapBuffers()

    def close(self):
        self.opengl_context = None
        self.opengl_canvas = None
        wx.Frame.Close(self)

    def full_screen(self, width, height):
        ndisp = wx.Display.GetCount()
        for i in range(ndisp):
            d = wx.Display(i)
            # TODO: Would like to use d.GetName() but it is empty string on Mac.
            if not d.IsPrimary():
                g = d.GetGeometry()
                s = g.GetSize()
                if s.GetWidth() == width and s.GetHeight() == height:
                    self.Move(g.GetX(), g.GetY())
                    self.SetSize(width, height)
                    break
        # self.EnableFullScreenView(True) # Not available in wxpython
        # TODO: full screen always shows on primary display.
#        self.ShowFullScreen(True)
