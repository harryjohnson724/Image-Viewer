from __future__ import division
import os
import wx
from PIL import Image
from pubsub import pub

##########################################################################
class ViewerFrame(wx.Frame):

#-------------------------------------------------------------------------
    def __init__(self, parent, title):
        '''
        Constructor
        '''
        super(ViewerFrame, self).__init__(parent, title=title)
        pub.subscribe(self.on_frame_resize,"resize")

        self.panel = ViewerPanel(self, wx.BORDER_RAISED)
        self.add_menu_bar()

#--------------------------------------------------------------------------
    def add_menu_bar(self):
        '''
        Adds a Menu bar to the frame with file and view menus
        '''
        self.displaySize = wx.DisplaySize()
        #print self.displaySize[0], self.displaySize[1]
        self.SetSize((self.displaySize[0])/2, (self.displaySize[1])/2)
        self.panel.Refresh()

        menuBar = wx.MenuBar()
        fileMenu = wx.Menu()
        viewMenu = wx.Menu()

        fileItemOpen = fileMenu.Append(wx.ID_OPEN, 'Open', 'Open Image')
        fileItemQuit = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')

        self.viewItemAspectRatio = viewMenu.Append(wx.ID_ANY, "Keep Aspect Ratio",kind=wx.ITEM_CHECK)
        
        menuBar.Append(fileMenu, '&File')
        menuBar.Append(viewMenu, '&View')

        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_MENU, self.on_quit, fileItemQuit)
        self.Bind(wx.EVT_MENU, self.on_browse, fileItemOpen)
        self.Bind(wx.EVT_MENU, self.aspect_ratio_check, self.viewItemAspectRatio)
          
#--------------------------------------------------------------------------
    def aspect_ratio_check(self, event):
        '''
        This Event is called when user checks 'Keep Aspect Ratio' in the menu.
        Handling is done at the panel
        '''
        if self.viewItemAspectRatio.IsChecked():
            keepAspectRatio = 1
        else:
            keepAspectRatio = 0
        pub.sendMessage("aspectRatio", message=keepAspectRatio)

#--------------------------------------------------------------------------
    def on_quit(self, e):
        '''
        This Event is called when user clicks the quit option in the menu.
        '''
        self.Close()
        exit()

#-------------------------------------------------------------------------- 
    def on_browse(self, event):
        ''' 
        Browse for file
        '''
        wildCard = "Pictures (*.tif,*.jpeg,*.png,*.jpg)|*.tif;*.jpeg;*.png;*.jpg"
        dialog = wx.FileDialog(None, "Choose a file",
                               wildcard=wildCard,
                               style=wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            imageFilePath = dialog.GetPath()
          
        dialog.Destroy()   
        pub.sendMessage("filepath", message=imageFilePath, arg2=self.displaySize)

#--------------------------------------------------------------------------   
    def on_frame_resize(self,message,arg2):
        '''
        resizes the frame 
        '''
        self.SetSize(message,arg2)


###########################################################################
class ViewerPanel(wx.Panel):

#--------------------------------------------------------------------------
    def __init__(self, parent, style):
        '''
        constructor
        '''

        super(ViewerPanel, self).__init__(parent,style=style)
        self.SetBackgroundColour('black')
        self.aspectRatioCheck = 0
        self.frameHeight = 500
        self.frameWidth  = 500

        self.create_widgets()
        pub.subscribe(self.display_image, "filepath")
        pub.subscribe(self.aspect_ratio_check, "aspectRatio")

#--------------------------------------------------------------------------
    def create_widgets(self):
        '''
        adds boxsizer and a static image to the panel
        '''
        self.img = wx.Image(500,500)
        self.imageCtrl = wx.StaticBitmap(self, wx.ID_ANY,
                                            wx.Bitmap(self.img))
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.imageCtrl, 0, wx.ALL, 5)
        self.SetSizerAndFit(self.mainSizer)
        self.mainSizer.Fit(self)
        self.Layout()

#-------------------------------------------------------------------------
    def is_image(self,filePath):
        '''
        check if the given path opens an image file
        '''
        try:
            Image.open(filePath)
        except IOError:
            return False
        return True

#--------------------------------------------------------------------------
    def check_aspect_ratio_and_draw_image(self,width,height):
        '''
        this function checks if the keep aspect ratio flag is checked
        and accordingly draws the image
        '''

        if self.aspectRatioCheck == 1:
            self.keep_aspect_ratio_and_draw_image(width, height)
        else:
            self.draw_image(width, height)        

#--------------------------------------------------------------------------
    def display_image(self, message, arg2):
        '''
        called when user selects an image file from the dialogue box.
        Basically draws the first version of the image
        '''
   
        #check if the given file is an image
        if not self.is_image(message):
            print "Given file is not an image"
            return False

        self.img = wx.Image(message, wx.BITMAP_TYPE_ANY)
        self.panelWidth, self.panelHeight = self.GetSize()
        self.check_aspect_ratio_and_draw_image(self.panelWidth, self.panelHeight)

        self.Bind(wx.EVT_SIZE, self.on_resize)
        return True

#--------------------------------------------------------------------------- 
    def aspect_ratio_check(self, message):
        '''
        checks if the aspect ratio option in the menu is checked and
        calls the appropriate function
        '''
        self.frameWidth, self.frameHeight = self.GetSize()

        if message == 1:
            self.aspectRatioCheck = 1
        else:
            self.aspectRatioCheck = 0

        self.check_aspect_ratio_and_draw_image(self.frameWidth, self.frameHeight)

#--------------------------------------------------------------------------
    def keep_aspect_ratio_and_draw_image(self, frameWidth, frameHeight):
        '''
        calculates the new width and height of the image according
        to the frame sizes passed. Aspect ratio is maintained during
        the calculation
        '''
        imageWidth, imageHeight = self.img.GetSize()
      
        imageRatio = imageWidth / imageHeight 
        frameRatio = frameWidth / frameHeight

        newImageWidth = 0.0000
        newImageHeight = 0.0000

        if frameRatio > imageRatio:
            newImageWidth = imageWidth * frameHeight / imageHeight
            newImageHeight = frameHeight

        elif imageRatio > frameRatio:
            newImageWidth = frameWidth 
            newImageHeight = imageHeight * frameWidth / imageWidth
    
        else:
            return True

        self.draw_image(newImageWidth , newImageHeight )

#--------------------------------------------------------------------------
    def on_resize(self, event):
        '''
        event is called when the user adjusts the frame
        '''

        self.frameWidth = event.Size.width
        self.frameHeight = event.Size.height
        self.check_aspect_ratio_and_draw_image(self.frameWidth, self.frameHeight)

#--------------------------------------------------------------------------
    def draw_image(self,width,height):
        '''
        this funtion draws the image on the panel
        to increase quality, give the wx.IMAGE_QUALITY_HIGH flag
        '''
        #print "panel size is",self.GetSize()
        
        try:
            self.scaledImg = self.img.Scale(width, height, quality=wx.IMAGE_QUALITY_NORMAL)
        except:
            print "Size below zero"
            return

        if self.aspectRatioCheck == 1:
            posX = (self.frameWidth - width)/2
            posY = (self.frameHeight- height)/2
            self.imageCtrl.SetPosition((posX, posY))
        else:
            self.imageCtrl.SetPosition((0, 0))
            
        self.imageCtrl.SetBitmap(wx.Bitmap(self.scaledImg))
        self.Refresh()


###########################################################################
class ImageViewerApp(wx.App):

#--------------------------------------------------------------------------
    def OnInit(self):
        self.frame = ViewerFrame(parent=None,title="Image Viewer frame")
        self.frame.Show()
        return True
    

##########################################################################
ImageViewer = ImageViewerApp()
ImageViewer.MainLoop()
    
