# -*- coding: utf-8 -*-
"""
	The main window - the glue that holds everything together
"""

from PyQt4 import QtCore, QtGui

from app.settings import settings
import app.Boards
import app.API

import app.utils

from gui.SettingsDialog import SettingsDialog
from gui.WebSitesDialog import WebSitesDialog

from gui.dockwidgets.HelpDock import HelpDock
from gui.dockwidgets.APIBrowserDock import APIBrowserDock

from gui.panes.APIBrowserPane import APIBrowserPane
from gui.panes.FileSystemBrowserPane import FileSystemBrowserPane

from gui.browser.BrowserWidget import Browser

from gui.BoardsDialog import BoardsDialog
from gui.BootLoadersDialog import BootLoadersDialog

from gui.widgets.ProjectsListWidgets import ProjectsBrowser
from gui.widgets.EditorWidget import EditorWidget

from gui.icons import Ico 
from gui.icons import Icon 

class MainWindow(QtGui.QMainWindow):
	"""
		Implements the main window
	"""
	def __init__(self, parent=None):
		QtGui.QMainWindow.__init__(self)

		# TODO - User customisable style
		QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))

		## Set the title text format
		self.title_text = "Dawn"

		## Sets up the settings and other global classes
		self.api = app.API.API()
		self.ut = None

		## Set Window Properties		
		self.setWindowTitle(self.title_text)
		self.setWindowIcon(Icon(Ico.Arduino))
		self.setMinimumWidth(800)
		self.setMinimumHeight(600)

		self.setDockNestingEnabled(True)
		self.setDockOptions(QtGui.QMainWindow.ForceTabbedDocks | QtGui.QMainWindow.VerticalTabs)

		self.topToolBar = QtGui.QToolBar()
		self.topToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
		self.addToolBar( self.topToolBar )

		##############################################################
		## File Menu
		##############################################################
		menuFile	= self.menuBar().addMenu( "File" )
		menuSettings = menuFile.addAction(Icon(Ico.Settings), "Settings", self.on_settings_dialog)
		menuFile.addSeparator()
		# TODO: Connect this to something
		menuExit = menuFile.addAction(Icon(Ico.Exit), "Exit", self.on_exit)
		#self.topToolBar.addAction(menuSettings)


		##############################################################
		## View Menu
		##############################################################
		menuView = self.menuBar().addMenu( "View")
		self.groupViewActions = QtGui.QActionGroup(self)
		self.connect(self.groupViewActions, QtCore.SIGNAL("triggered (QAction *)"), self.on_action_view)

		views = []
		views.append(['projects', Ico.Projects, "Projects"])
		views.append(['api_browser', Ico.Function, "API Browser"])
		views.append(['help', Ico.Help, "Help"])
		views.append(['file_system_browser', Ico.FileSystemBrowser, "Files Browser"])

		for ki, ico, caption in views:
			act = menuView.addAction(Icon(ico), caption)
			act.setProperty("ki", ki)
			self.topToolBar.addAction(act)
			self.groupViewActions.addAction(act)
		self.topToolBar.addSeparator()
		menuView.addAction("View Help in dock - TODO")
		menuView.addAction("View something else in dock")

		##############################################################
		## Projects Menu
		##############################################################
		menuProjects  = self.menuBar().addMenu( "Projects" )
		## TODO populate this menu

		##############################################################
		## Hardware Menu
		##############################################################
		menuHardware 	= self.menuBar().addMenu( "Hardware" )

		## Boards
		self.actionGroupBoards = QtGui.QActionGroup(self)
		self.actionGroupBoards.setExclusive(True)
		self.connect(self.actionGroupBoards, QtCore.SIGNAL("triggered(QAction *)"), self.on_action_select_board)
		self.menuBoards = menuHardware.addMenu(Icon(Ico.Board), "-- No Board Selected --") # populates later
		act = menuHardware.addAction(Icon(Ico.Boards), "Boards", self.on_action_boards)
		self.topToolBar.addAction(act)
		menuHardware.addSeparator()

		## Bootloaders
		self.actionGroupBootLoaders = QtGui.QActionGroup(self)
		self.actionGroupBootLoaders.setExclusive(True)
		self.connect(self.actionGroupBootLoaders, QtCore.SIGNAL("triggered(QAction *)"), self.on_action_bootloader_burn)
		self.menuBootLoaders = menuHardware.addMenu(Icon(Ico.BootLoaderBurn), "Burn Bootloader") # populates later
		act = menuHardware.addAction(Icon(Ico.BootLoaders), "Bootloaders", self.on_action_bootloaders)
		self.topToolBar.addAction(act)
		self.topToolBar.addSeparator()

		##############################################################
		## Websites Menu
		##############################################################
		self.menuWebSites 	= self.menuBar().addMenu("Websites" )
	
		self.menuWebSites.addSeparator()
		self.actionEditWebsites = self.menuWebSites.addAction( "Edit Sites", self.on_websites_dialog )

		##############################################################
		## Help Menu
		menuHelp 	= self.menuBar().addMenu( "Help" )
		menuHelp.addAction( "About This Project", self.on_about)
		menuHelp.addAction( "About Qt", self.on_about_qt)


		####################################
		## Dock Widgets
		####################################
		helpDockWidget = HelpDock("Help", self, self)
		self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, helpDockWidget)
		
		##########################################################
		## Central Widget
		##########################################################

		self.mainTabWidget = QtGui.QTabWidget(self)
		self.mainTabWidget.setTabsClosable(True)
		self.mainTabWidget.setMovable(True)
		self.setCentralWidget(self.mainTabWidget)
		self.connect(self.mainTabWidget, QtCore.SIGNAL("tabCloseRequested (int)"), self.on_close_tab_requested)
		self.connect(self.mainTabWidget, QtCore.SIGNAL("currentChanged (int)"), self.on_tab_change)

		## Load Projects and Welcome
		self.on_open_project(settings.app_path().absoluteFilePath("etc/example_project/example.pde"))
		self.on_action_view(QtCore.QString("welcome"))
		self.on_action_view(QtCore.QString("projects"))
		self.mainTabWidget.setCurrentIndex(0)	
		##########################################################
		## Status Bar
		##########################################################
		self.statusBar().addPermanentWidget(QtGui.QLabel("Board:"))
		self.lblBoard = QtGui.QLabel("-- none --")
		self.statusBar().addPermanentWidget(self.lblBoard)

		##########################################################
		## Globally Shared Widgets
		##########################################################

		## Borads
		self.boards = app.Boards.Boards(self)
		self.connect(self.boards, QtCore.SIGNAL("board_selected"), self.on_board_selected)
		self.boards.load_current() ## THIS actually sets current as event above is not fired in constructor


		## API
		
		if not settings.value("virginity"):
			self.on_settings_dialog()

		settings.restore_window( "main_window", self )
		self.on_refresh_settings()


	#########################################
	## View  Actions
	def on_action_view(self, strOrObject):
		"""
			Creates a new tab
		"""
		#TODO: Banish this! 
		if isinstance(strOrObject, QtCore.QString):
			ki = strOrObject
		else:
			ki = strOrObject.property("ki").toString()
		idx = None

		if ki == 'api_browser':
			apiBrowser = APIBrowserPane(self, self)
			idx = self.mainTabWidget.addTab(apiBrowser, Icon(Ico.Function), "API Browser")


		elif ki == "file_system_browser":
			fileSystemBrowser = FileSystemBrowserPane(self, self)
			idx = self.mainTabWidget.addTab(fileSystemBrowser, Icon(Ico.FileSystemBrowser), "Files Browser")

		elif ki == 'projects':
			projectsWidget = ProjectsBrowser( self, self )
			idx = self.mainTabWidget.addTab(projectsWidget, Icon(Ico.Projects), "Projects")
			self.connect(projectsWidget, QtCore.SIGNAL("open_project"), self.on_open_project)

		elif ki == 'welcome':
			welcomePage = Browser(self, self, initial_page="file://%s" % settings.html_pages_path().absoluteFilePath("welcome.html"))
			self.mainTabWidget.addTab(welcomePage, Icon(Ico.Arduino), "Welcome")

		if idx:
			self.mainTabWidget.setCurrentIndex(idx)

	#########################################
	## Board Stuff
	def on_action_boards(self):
		d = BoardsDialog(self, self)
		d.show()

	def on_action_select_board(self, act):
		self.boards.set_current(act.property("board").toString())

	def on_board_selected(self, board):
		self.lblBoard.setText(board['name'])
		self.menuBoards.setTitle(board['name'])

	#########################################
	## Bootloader Stuff
	def on_action_bootloaders(self):
		d = BootLoadersDialog(self, self)
		d.show()

	def on_action_bootloader_burn(self, act):
		pass


	#########################################
	## Tab Events
	def on_close_tab_requested(self, tabIndex):
		self.mainTabWidget.removeTab(tabIndex)

	def on_tab_change(self, index):
		self.setWindowTitle(self.title_text % self.mainTabWidget.tabText(index))

	#########################################
	## Open Project
	def on_open_project(self, file_path):
		fileInfo = QtCore.QFileInfo(file_path)
		newEditor = EditorWidget(self, self, arduino_mode=True)
		newEditor.load_file(fileInfo.filePath())
		newTab = self.mainTabWidget.addTab(newEditor, Icon(Ico.Project), fileInfo.fileName())
		self.mainTabWidget.setCurrentIndex(newTab)


	def on_dev_load_keywords(self):
		import app.keywords
		
		keyw = app.keywords.Keywords(self)

	def on_settings_dialog(self):
		d = SettingsDialog(self, self)
		self.connect(d, QtCore.SIGNAL("refresh_settings"), self.on_refresh_settings)
		if d.exec_():
			self.on_refresh_settings()

	def on_refresh_settings(self):
		
		## Load Boards Menu
		for act in self.actionGroupBoards.actions():
			self.actionGroupBoards.removeAction(act)
		current = self.boards.current()
		if current:
			current = current['name']
		for board, caption in self.boards.index():
			act = self.menuBoards.addAction( caption )
			act.setProperty("board", board )
			act.setCheckable(True)
			if board == current:
				act.setChecked(True)
			self.actionGroupBoards.addAction(act)

		## Laod bootloaders
		for act in self.actionGroupBootLoaders.actions():
			self.actionGroupBootLoaders.removeAction(act)
		file_path = settings.hardware_path().absoluteFilePath("programmers.txt")
		if QtCore.QFileInfo(file_path).exists():
			dic = app.utils.load_arduino_config_file(file_path)
			for ki in dic:
				act = self.menuBootLoaders.addAction( ki )
				act.setCheckable(True)
				self.actionGroupBootLoaders.addAction(act)

			

	def on_websites_dialog(self):
		d = WebSitesDialog(self, self)
		d.show()

	##########################################################
	## About and Quit
	##########################################################
	def on_about(self):
		QtGui.QMessageBox.about(self, "TODO", "LINK to google project page")

	def on_about_qt(self):
		QtGui.QMessageBox.aboutQt(self)

	def closeEvent(self, event ):
		settings.save_window( "main_window", self )

	def on_exit(self):
		#TODO
		## Crash me
		print "Bye"
