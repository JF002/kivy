'''
EGL Rpi Window: EGL Window provider, specialized for the Pi
'''

__all__ = ('WindowEglRpi', )

from kivy.logger import Logger
from kivy.core.window import WindowBase
from kivy.base import EventLoop, stopTouchApp, ExceptionManager
from ctypes import *

# https://bitbucket.org/bryancole/rpi_vid_core/overview
from vidcore import vg, egl, bcm 
from kivy.graphics.opengl import *

_c = egl._constants

        
class WindowEglRpi(WindowBase):
    def create_window(self):
        self._fakeMouseX = 0
        self._fakeMouseY = 0
        bcm.host_init()
        W,H = bcm.graphics_get_display_size(0)
        self._size[0] = int(W)
        self._size[1] = int(H)
        self.win = self._create_window(self._size[0], self._size[1])
        self.dpy, self.surf, self.ctx = self._make_egl_context(self.win, 0)
        glBindFramebuffer(0x8D40,0) # 0x8D40 = GL_FRAMEBUFFER
        super(WindowEglRpi, self).create_window()

    def flip(self):
        egl.SwapBuffers(self.dpy, self.surf)
        super(WindowEglRpi, self).flip()
        
    def _mainloop(self):
        EventLoop.idle()
        
        self.dispatch('on_mouse_move', self._fakeMouseX, self._fakeMouseY, self.modifiers)
        self._fakeMouseX = self._fakeMouseX+1;
        self._fakeMouseY = self._fakeMouseY+1;
        
        
    
    def mainloop(self):
        while not EventLoop.quit and EventLoop.status == 'started':
            try:
                self._mainloop()
            except BaseException, inst:
                # use exception manager first
                r = ExceptionManager.handle_exception(inst)
                if r == ExceptionManager.RAISE:
                    stopTouchApp()
                    raise
                else:
                    pass
                    
    def _create_window(self, width, height):
        W,H=width,height 
        dst = bcm.Rect(0,0,W,H)
        src = bcm.Rect(0,0,W<<16,H<<16)
        display = egl.bcm_display_open(0)
        update = egl.bcm_update_start(0)
        element = egl.bcm_element_add(update, display, 0, dst, src)
        win = egl.NativeWindow(element, W, H)
        egl.bcm_update_submit_sync(update)
        return win
            
        
    def _make_egl_context(self, win, flags):
        api = egl._constants.EGL_OPENGL_ES_API
        attribs = [_c.EGL_RED_SIZE,       8,
           _c.EGL_GREEN_SIZE,     8,
           _c.EGL_BLUE_SIZE,      8,
           _c.EGL_ALPHA_SIZE,     8,
           _c.EGL_DEPTH_SIZE,     _c.EGL_DONT_CARE,
           _c.EGL_STENCIL_SIZE,   _c.EGL_DONT_CARE,
           _c.EGL_SAMPLE_BUFFERS,  0,
           _c.EGL_NONE]
        
        attribsContext = [
            _c.EGL_CONTEXT_CLIENT_VERSION, 2,
            _c.EGL_NONE]   
        
        display = egl.GetDisplay(_c.EGL_DEFAULT_DISPLAY)
        major, minor = egl.Initialise(display)
        egl.BindAPI(_c.EGL_OPENGL_ES_API)
        N = egl.GetConfigs(display)
        config = egl.ChooseConfig(display, attribs, 1)[0]
        surface = egl.CreateWindowSurface(display, config, win)
        context = egl.CreateContext(display, config, None,attribsContext)
        egl.MakeCurrent(display, surface, surface, context)
        return (display, surface, context)