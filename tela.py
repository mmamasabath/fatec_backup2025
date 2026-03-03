#-------------biblioteca----------------
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
#----------------------------------------

#----------classe de container de wigts------
class Container(BoxLayout):
	pass
#---------------------------------------------

#------------classe da tela principal---------
class Tela(App):
	def build(self):
		return Container() 	
	
	def fuck(self):
		print("fuck") 
#----------------------------------------------

Tela().run()
