#----------------------------------------------------------------------#
# ApproxSRPTE.py
#
# This application simulates a single server with Poisson arrivals
# and processing times of a general distribution. There are errors in
# time estimates within a range. Arrivals are assigned to SRPT classes
# using the methods described in Adaptive and Scalable Comparison
# Scheduling.
#
# Rachel Mailach
#----------------------------------------------------------------------#

from tkinter import *
#from tkinter import messagebox
from tkinter import ttk 
from tkinter import filedialog
from datetime import datetime

from math import log
import plotly.plotly as py
from plotly.graph_objs import Scatter
import plotly.graph_objs as go
#from bokeh.plotting import figure, output_file, show
#from bokeh.charts import Bar, output_file, show
#from collections import OrderedDict

import copy
import random
import csv
import operator

import sqlite3
import pandas

conn=sqlite3.connect('SingleServerDatabase_ASRPTE.db')

NumJobs = []
AvgNumJobs = []
NumJobsTime = []

#----------------------------------------------------------------------#
# Class: GUI
#
# This class is used as a graphical user interface for the application.
#
#----------------------------------------------------------------------#
class GUI(Tk):
	def __init__(self, master):
		Tk.__init__(self, master)
		self.master = master        # reference to parent
		self.statusText = StringVar()
		global SEED
		#SEED = random.randint(0, 1000000000)
		SEED = 994863731
		random.seed(SEED)
		

		# Create the input frame
		self.frameIn = Input(self)
		self.frameIn.pack(side=TOP, fill=X, expand=False, padx = 5, pady =5, ipadx = 5, ipady = 5)     

		# Create the output frame
		self.frameOut = Output(self)
		self.frameOut.pack(side=TOP, fill=BOTH, expand=True, padx = 5, pady =5, ipadx = 5, ipady = 5)

		# Bind simulate button
		self.bind("<<input_simulate>>", self.submit)

		# Bind save button
		self.bind("<<output_save>>", self.saveData)

		# Bind clear button
		self.bind("<<output_clear>>", self.clearConsole)

		# Bind stop button
		self.bind("<<stop_sim>>", self.stopSimulation)		

		# Status Bar
		status = Label(self.master, textvariable=self.statusText, bd=1, relief=SUNKEN, anchor=W)
		status.pack(side=BOTTOM, anchor=W, fill=X)      

		# Initialize console
		self.consoleFrame = Frame(self.frameOut)
		self.console = Text(self.consoleFrame, wrap = WORD)		
		self.makeConsole()
		self.printIntro()
		self.updateStatusBar("Waiting for submit...")

	def makeConsole(self):
		#self.consoleFrame = Frame(self.frameOut)
		self.consoleFrame.pack(side=TOP, padx=5, pady=5)
		#self.console = Text(self.consoleFrame, wrap = WORD)
		self.console.config(state=DISABLED)     # start with console as disabled (non-editable)
		self.scrollbar = Scrollbar(self.consoleFrame)
		self.scrollbar.config(command = self.console.yview)
		self.console.config(yscrollcommand=self.scrollbar.set)
		self.console.grid(column=0, row=0)
		self.scrollbar.grid(column=1, row=0, sticky='NS')

		#DOES NOTHING??
		self.grid_columnconfigure(0, weight=1) 
		self.grid_rowconfigure(0, weight=1)


	def writeToConsole(self, text = ' '):
		self.console.config(state=NORMAL)       # make console editable
		self.console.insert(END, '%s\n'%text)
		self.update()
		self.console.yview(END)					# auto-scroll		
		self.console.config(state=DISABLED)     # disable (non-editable) console

	def saveData(self, event):
		# Get filename
		filename = fileDialog.asksaveasfilename(title="Save as...", defaultextension='.txt')
		
		if filename:
			file = open(filename, mode='w')
			data = self.console.get(1.0, END)
			encodedData = data.encode('utf-8')
			text = str(encodedData)
		
			file.write(text)

			file.close()

	# Empty arrivals file at the begining of each simulation
	def clearSavedArrivals(self):
		with open("Arrivals.txt", "w") as myFile:
			myFile.write('JOB NAME,    ARRIVAL TIME,    RPT,     ERPT,     CLASS' + '\n')
		myFile.close()

	def clearConsole(self, event):
		self.console.config(state=NORMAL)       # make console editable
		self.console.delete('1.0', END)
		self.console.config(state=DISABLED)     # disable (non-editable) console

	def updateStatusBar(self, text=' '):
		self.statusText.set(text)
	
	def printIntro(self):
		self.writeToConsole("Approximate SRPTE \n\n This application simulates a single server with Poisson arrivals and processing times of a general distribution. There are errors in time estimates within a range. Arrivals are assigned to SRPT classes using the methods described in Adaptive and Scalable Comparison Scheduling.")

	def printParams(self, load, arrDist, procRate, procDist, percErrorMin, percErrorMax, numClasses, simLength): 
		self.writeToConsole("--------------------------------------------------------------------------------")
		self.writeToConsole("PARAMETERS:")
		self.writeToConsole("Load = %.4f"%load)
		#self.writeToConsole("Arrival Rate = %.4f"%arrRate)
		self.writeToConsole("Arrival Distribution = %s"%arrDist)
		self.writeToConsole("Processing Rate = %.4f, Processing Distribution = %s"%(procRate, str(procDist)))
		self.writeToConsole("% Error  = " + " %.4f, %.4f"%(percErrorMin, percErrorMax))
		self.writeToConsole("Number of Classes = %d"%numClasses)
		self.writeToConsole("Simulation Length = %.4f"%simLength)

	def saveParams(self, load, arrRate, arrDist, procRate, procDist, percErrorMin, percErrorMax, numClasses, simLength, alpha, lower, upper):
		##params = pandas.DataFrame(columns=('seed', 'numServers', 'load', 'arrRate', 'arrDist', 'procRate', 'procDist', 'alpha', 'lower', 'upper', 'percErrorMin', 'percErrorMax', 'simLength'))
		print (SEED)
		params = pandas.DataFrame({	'seed' : [SEED],
									'load' : [load],
									'arrRate' : [arrRate],
									'arrDist' : [arrDist],
									'procRate' : [procRate],
									'procDist' : [procDist],
									'alpha' : [alpha],
									'lower' : [lower],
									'upper' : [upper],
									'percErrorMin' : [percErrorMin],
									'percErrorMax' : [percErrorMax],
									'numClasses' : [numClasses],
									'simLength' : [simLength],
									'avgNumJobs' : [MachineClass.AvgNumJobs]
									})

		params.to_sql(name='parameters', con=conn, if_exists='append')
		print (params)

	# def plotNumJobsInSys(self, numClasses):
	# 	# SCATTER PLOT
	# 	output_file("Scatter_Case24")
	# 	scatter = figure(title = "Average Number of Jobs Over Time",
	# 					x_axis_label = "Time",
	# 					y_axis_label = "Number of Jobs")
	# 	#trace0.scatter(NumJobsTime, NumJobs)
	# 	scatter.line(NumJobsTime, NumJobs)
	# 	scatter.circle(NumJobsTime, NumJobs, size=1)
	# 	show(scatter)


 
	# 	#-----------------------------------------------------------------------------#
	# 	# BLOCK DIAGRAM
	# 	output_file("Bar_Case24")

	# 	classRange = range(1, numClasses + 1)
	# 	classes = [format(i,'02d') for i in classRange]

	# 	# remove placeholder element
	# 	MachineClass.AvgNumJobsArray.pop(0)

	# 	dictionary = {'number of jobs': MachineClass.AvgNumJobsArray, 'classes': classes}
	# 	df = pandas.DataFrame(data=dictionary)

	# 	bar = Bar(df, 'classes', values='number of jobs', title="Average Number of Jobs Per Class")
	# 	show(bar)
	def plotNumJobsInSys(self):
		py.sign_in('mailacrs','wowbsbc0qo')
		trace0 = Scatter(x=NumJobsTime, y=NumJobs)
		data = [trace0]
		layout = go.Layout(
			title='Number of Jobs Over Time',
			xaxis=dict(
				title='Time',
				titlefont=dict(
				family='Courier New, monospace',
				size=18,
				color='#7f7f7f'
			)
		),
			yaxis=dict(
				title='Number of Jobs',
				titlefont=dict(
				family='Courier New, monospace',
				size=18,
				color='#7f7f7f'
			)
		)
		)
		fig = go.Figure(data=data, layout=layout)
		unique_url = py.plot(fig, filename = 'ClassBased_NumJobs')

	def plotAvgNumJobsInSys(self, numClasses):
		py.sign_in('mailacrs','wowbsbc0qo')
		trace0 = Scatter(x=NumJobsTime, y=AvgNumJobs)
		data = [trace0]
		layout = go.Layout(
			title='Average Number of Jobs Over Time',
			xaxis=dict(
				title='Time',
				titlefont=dict(
				family='Courier New, monospace',
				size=18,
				color='#7f7f7f'
			)
		),
			yaxis=dict(
				title='Number of Jobs',
				titlefont=dict(
				family='Courier New, monospace',
				size=18,
				color='#7f7f7f'
			)
		)
		)
		fig = go.Figure(data=data, layout=layout)
		unique_url = py.plot(fig, filename = 'ClassBased_AvgNumJobs')

		#-----------------------------------------------------------------------------#
		# Average jobs/class
		trace1 = go.Bar(y= MachineClass.AvgNumJobsArray)
		
		data1 = [trace1]
		layout1 = go.Layout(
			title='Average Number of Jobs Per Class',
			xaxis=dict(
				title='Classes',
				range=[0.5,numClasses+0.5],              # set range
				titlefont=dict(
				family='Courier New, monospace',
				size=18,
				color='#7f7f7f'
			)
		),
			yaxis=dict(
				title='Number of Jobs',
				titlefont=dict(
				family='Courier New, monospace',
				size=18,
				color='#7f7f7f'
			)
		)
		)
		fig1 = go.Figure(data=data1, layout=layout1)
		unique_url1 = py.plot(fig1, filename = 'ClassBased_NumJobsPerClass')

	def calcVariance(self, List, avg):
		var = 0
		for i in List:
			var += (avg - i)**2
		return var/len(List)

	def stopSimulation(self, event):
		MachineClass.StopSim = True
				
	def submit(self, event):
		self.updateStatusBar("Simulating...")
		self.clearSavedArrivals()
		I = Input(self)     

		self.printParams(I.valuesList[0],					#load
						 'Exponential',						#arrival
						 I.valuesList[2], I.distList[1], 	#processing rate
						 I.valuesList[3],					#error min
						 I.valuesList[4],					#error max
						 I.valuesList[5], 					#num Classes
						 I.valuesList[6])					#sim time
		main.timesClicked = 0
		
		# Start process
		MC = MachineClass(self)
		MC.run(	I.valuesList[0],				#load
				'Exponential',					#arrival
				I.valuesList[2], I.distList[1],	# proc
				I.valuesList[3],				# error min
				I.valuesList[4],				# error max
				I.valuesList[5],				# num class
				I.valuesList[6])				# sim time

		self.saveParams(I.valuesList[0],		#load
					'?', 				# arrival rate
					'Exponential',					# arrival dist
					'?', I.distList[1],	# processing
					I.valuesList[3], 				# error min
					I.valuesList[4],				# error max
					I.valuesList[5], 				# num classes
					I.valuesList[6],				# sim time
					JobClass.BPArray[0],			# alpha
					JobClass.BPArray[1],			# lower
					JobClass.BPArray[2])			# upper		

		#self.plotNumJobsInSys()
		#self.plotAvgNumJobsInSys(I.valuesList[5])
		#self.saveData(event)
		self.updateStatusBar("Simulation complete.")


#----------------------------------------------------------------------#
# Class: Input
#
# This class is used as a graphical user interface for a larger
# application.
#
#----------------------------------------------------------------------#
class Input(LabelFrame):
	def __init__(self, master):
		LabelFrame.__init__(self, master, text = "Input")
		self.master = master
		self.loadInput = DoubleVar()
		self.arrivalRateInput = DoubleVar()
		self.processingRateInput = DoubleVar()
		self.percentErrorMinInput = DoubleVar()
		self.percentErrorMaxInput = DoubleVar()
		self.numberOfClassesInput = IntVar()
		self.simLengthInput = DoubleVar()
		self.errorMessage = StringVar()
		self.comboboxVal = StringVar()

		self.loadInput.set(0.95)       		 	   	##################################CHANGE LATER
		#self.arrivalRateInput.set(1.0)         	 ##################################CHANGE LATER
		self.processingRateInput.set(0.5)   	    ##################################CHANGE LATER
		self.percentErrorMinInput.set(0)          ##################################CHANGE LATER
		self.percentErrorMaxInput.set(0)          ##################################CHANGE LATER
		self.numberOfClassesInput.set(2)			##################################CHANGE LATER
		self.simLengthInput.set(50.0)           ##################################CHANGE LATER

		self.grid_columnconfigure(0, weight=2)
		self.grid_columnconfigure(1, weight=2)
		self.grid_columnconfigure(2, weight=1)
		self.grid_columnconfigure(3, weight=1)
		self.grid_columnconfigure(4, weight=1)
		self.grid_columnconfigure(5, weight=2)
		self.grid_rowconfigure(0, weight=1)

		# Labels
		labels = ['System Load', 'Interarrival Rate (' + u'\u03bb' + ')', 'Processing Rate (' + u'\u03bc' + ')', '% Error', 'Number of Classes', 'Simulation Length']
		r=0
		c=0
		for elem in labels:
			Label(self, text=elem).grid(row=r, column=c)
			r=r+1
		
		Label(self, textvariable=self.errorMessage, fg="red", font=14).grid(row=6, columnspan=4) #error message, invalid input
		#Label(self, text=u"\u00B1").grid(row=3, column=1) # +/-
		Label(self, text="Min").grid(row=3, column=1, sticky = E) 
		Label(self, text="Max").grid(row=3, column=3, sticky = W) 

		# Entry Boxes
		self.entry_0 = Entry(self, textvariable = self.loadInput)
		self.entry_1 = Entry(self, textvariable = self.arrivalRateInput)
		self.entry_2 = Entry(self, textvariable = self.processingRateInput)
		self.entry_3a = Entry(self, textvariable = self.percentErrorMinInput, width = 5)
		self.entry_3b = Entry(self, textvariable = self.percentErrorMaxInput, width = 5)
		self.entry_4 = Entry(self, textvariable = self.numberOfClassesInput)
		self.entry_5 = Entry(self, textvariable = self.simLengthInput)
		self.entry_0.grid(row = 0, column = 1, columnspan = 4)	
		self.entry_1.grid(row = 1, column = 1, columnspan = 4)
		self.entry_2.grid(row = 2, column = 1, columnspan = 4)
		self.entry_3a.grid(row = 3, column = 2, sticky = E)
		self.entry_3b.grid(row = 3, column = 4, sticky = W)
		self.entry_4.grid(row = 4, column = 1, columnspan = 4)
		self.entry_5.grid(row = 5, column = 1, columnspan = 4)
		self.loadInput.trace('w', self.entryBoxChange)
		self.arrivalRateInput.trace('w', self.entryBoxChange)
		self.refreshLoad()

		# Distribution Dropdowns
		self.distributions = ('Select Distribution', 'Poisson', 'Exponential', 'Uniform', 'Bounded Pareto', 'Custom')
		self.comboBox_1 = ttk.Combobox(self, values = self.distributions, state = 'disabled')
		self.comboBox_1.current(2) # set selection
		self.comboBox_1.grid(row = 1, column = 5)
		self.comboBox_2 = ttk.Combobox(self, textvariable = self.comboboxVal, values = self.distributions, state = 'readonly')
		self.comboBox_2.current(4) # set default selection                  #####################CHANGE LATER
		self.comboBox_2.grid(row = 2, column = 5)

		self.comboboxVal.trace("w", self.selectionChange) # refresh on change
		self.refreshComboboxes()		

		# Simulate Button
		self.simulateButton = Button(self, text = "SIMULATE", command = self.onButtonClick)
		self.simulateButton.grid(row = 7, columnspan = 6)

	def entryBoxChange(self, name, index, mode):
		self.refreshLoad()

	def refreshLoad(self):
		if len(self.entry_0.get()) > 0:
			self.entry_1.delete(0, 'end')
			self.entry_1.configure(state = 'disabled')
		else:
			self.entry_1.configure(state = 'normal')

		if len(self.entry_1.get()) > 0:
			self.entry_0.delete(0, 'end')
			self.entry_0.configure(state = 'disabled')
		else:
			self.entry_0.configure(state = 'normal')

	def selectionChange(self, name, index, mode):
		self.refreshComboboxes()

	def refreshComboboxes(self):
		selection = self.comboBox_2.get()
		if selection == 'Bounded Pareto':
			self.entry_2.configure(state = 'disabled')
		else:
			self.entry_2.configure(state = 'normal')		

	def onButtonClick(self):
		if (self.getNumericValues() == 0) and (self.getDropDownValues() == 0):
				# Send to submit button in main 
				self.simulateButton.event_generate("<<input_simulate>>")


	def getNumericValues(self):
		try:
				load = self.loadInput.get()
				#arrivalRate = self.arrivalRateInput.get()
				processingRate = self.processingRateInput.get()
				percentErrorMin = self.percentErrorMinInput.get()
				percentErrorMax = self.percentErrorMaxInput.get()
				numClasses = self.numberOfClassesInput.get()
				maxSimLength = self.simLengthInput.get()
		except ValueError:
				self.errorMessage.set("One of your inputs is an incorrect type, try again.")
				return 1

		# try:
		# 	arrRate = float(self.arrivalRateInput.get())
		# except ValueError:
		# 	arrRate = 0.0
		# try:
		# 	procRate = float(self.processingRateInput.get())
		# except ValueError:
		# 	procRate = 0.0

		if load <= 0.0:
				self.errorMessage.set("Load must be non-zero value!")
				return 1
		#if arrivalRate <= 0.0:
		#		self.errorMessage.set("Arrival rate must be non-zero value!")
		#		return 1
		#if processingRate <= 0.0:
		#		self.errorMessage.set("Processing rate must be non-zero value!")
		#		return 1
		if numClasses < 1.0:
				self.errorMessage.set("There must be at least one class!")
				return 1		
		if maxSimLength <= 0.0:
				self.errorMessage.set("Simulation length must be non-zero value!")
				return 1
		else:
				self.errorMessage.set("")
				Input.valuesList = [load, 0.0, processingRate, percentErrorMin, percentErrorMax, numClasses, maxSimLength]
				return 0

	def getDropDownValues(self):
		comboBox1Value = self.comboBox_1.get()
		comboBox2Value = self.comboBox_2.get()
		if comboBox2Value == 'Select Distribution':
				self.errorMessage.set("You must select a distribution for the processing rate")
				return 1
		else:
				self.errorMessage.set("")
				Input.distList = [comboBox1Value, comboBox2Value]
				return 0

#----------------------------------------------------------------------#
# Class: Output
#
# This class is used as a graphical user interface for a larger
# application.
#
#----------------------------------------------------------------------#
class Output(LabelFrame):
	def __init__(self, master):
		LabelFrame.__init__(self, master, text = "Output")
		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(0, weight=1)

		buttonFrame = Frame(self)
		buttonFrame.pack(side=BOTTOM, padx=5, pady=5)

		# Clear Button
		self.clearButton = Button(buttonFrame, text = "CLEAR DATA", command = self.onClearButtonClick)
		self.clearButton.grid(row = 2, column = 0)
		
		# Save Button
		self.saveButton = Button(buttonFrame, text = "SAVE DATA", command = self.onSaveButtonClick)
		self.saveButton.grid(row=2, column=1)

		# Stop Button
		self.stopButton = Button(buttonFrame, text = "STOP SIMULATION", command = self.onStopButtonClick)
		self.stopButton.grid(row = 2, column = 2)		

	def onClearButtonClick(self):
		# Clear console
		self.clearButton.event_generate("<<output_clear>>")

	def onSaveButtonClick(self):
		# Save data
		self.saveButton.event_generate("<<output_save>>")

	def onStopButtonClick(self):
		# Stop simulation
		self.stopButton.event_generate("<<stop_sim>>")

#----------------------------------------------------------------------#
# Class: CustomDist
#
# This class is used to allow users to enter a custom distribution.
#
#----------------------------------------------------------------------#
class CustomDist(object):
	def __init__(self, master):
		top = self.top = Toplevel(master)
		top.geometry("500x200")                     # set window size
		top.resizable(0,0)

		self.function = StringVar()

		# Label frame
		frame1 = Frame(top)
		frame1.pack(side=TOP, padx=5, pady=5)
		self.l=Label(frame1, text="Please enter the functional inverse of the distribution of your choice. \nExponential distribution is provided as an example. \nNote: x " + u"\u2265" + " 0", font=("Helvetica", 12), justify=LEFT)
		self.l.pack()

		# Button frame
		frame2 = Frame(top)
		frame2.pack(side=TOP, padx=5, pady=5)
		self.mu=Button(frame2, text=u'\u03bc', command=self.insertMu)
		self.mu.pack(side=LEFT)

		self.x=Button(frame2, text="x", command=self.insertX)
		self.x.pack(side=LEFT)

		self.ln=Button(frame2, text="ln", command=self.insertLn)
		self.ln.pack(side=LEFT)

		# Input frame
		frame3 = Frame(top)
		frame3.pack(side=TOP, padx=5, pady=5)
		self.e = Entry(frame3, textvariable = self.function)
		self.e.insert(0, "-ln(1 - x)/" + u'\u03bc')
		self.e.pack(fill="both", expand=True)

		frame4 = Frame(top)
		frame4.pack(side=TOP, pady=10)
		self.b=Button(frame4,text='Ok',command=self.cleanup)
		self.b.pack()

	def cleanup(self):
		self.stringEquation=self.convertFunction()
		self.top.destroy()

	def insertMu(self):
		self.e.insert(END, u'\u03bc')

	def insertX(self):
		self.e.insert(END, "x")

	def insertLn(self):
		self.e.insert(END, "ln")

	def convertFunction(self):
		self.stringList = list(self.e.get())
		for i in range(len(self.stringList)):
			if self.stringList[i] == u'\u03bc':
				self.stringList[i] = "procRate"
			elif self.stringList[i] == "x":
				self.stringList[i] = "random.uniform(0.0, 1.0)"
			elif self.stringList[i] == "l" and self.stringList[i+1] == "n":
				self.stringList[i] = "log"
				self.stringList[i+1] = ""
		print ("".join(self.stringList))
		return "".join(self.stringList)


#----------------------------------------------------------------------#
# Class: BoundedParetoDist
#
# This class is used to allow users to enter parameters to 
# Bounded Pareto distribution.
#
#----------------------------------------------------------------------#
class BoundedParetoDist(object):
	Array = []
	def __init__(self, master):
		top = self.top = Toplevel(master)
		top.geometry("500x200")                     # set window size
		top.resizable(0,0)
		
		self.errorMessage = StringVar()

		self.alpha = DoubleVar()
		self.L = DoubleVar()
		self.U = DoubleVar()

		# Set default parameters
		self.alpha.set(1.1)
		self.L.set(1)
		self.U.set(10**(6))

		# Label frame
		frame1 = Frame(top)
		frame1.pack(side=TOP, padx=5, pady=5)
		self.l=Label(frame1, text="Please enter the parameters you would like.", font=("Helvetica", 12), justify=LEFT)
		self.l.pack()
		self.error = Label(frame1, textvariable=self.errorMessage, fg="red", font=14)
		self.error.pack()

		# Input frame
		frame2 = Frame(top)
		frame2.pack(side=TOP, padx=5, pady=5)

		frame2.grid_columnconfigure(0, weight=1)
		frame2.grid_rowconfigure(0, weight=1)

		self.l1 = Label(frame2, text = "alpha (shape)")
		self.l2 = Label(frame2, text = "L (smallest job size)")
		self.l3 = Label(frame2, text = "U (largest job size)")
		self.l1.grid(row = 0, column = 0)
		self.l2.grid(row = 1, column = 0)
		self.l3.grid(row = 2, column = 0)

		self.e1 = Entry(frame2, textvariable = self.alpha)
		self.e2 = Entry(frame2, textvariable = self.L)		
		self.e3 = Entry(frame2, textvariable = self.U)		
		self.e1.grid(row = 0, column = 1)
		self.e2.grid(row = 1, column = 1)
		self.e3.grid(row = 2, column = 1)		

		frame3 = Frame(top)
		frame3.pack(side=TOP, pady=10)
		self.b=Button(frame3,text='Ok',command=self.cleanup)
		self.b.pack()

	def cleanup(self):
		if(self.checkParams() == 0):
			self.paramArray=BoundedParetoDist.Array
			self.top.destroy()

	def checkParams(self):
		self.a = float(self.e1.get())
		self.l = float(self.e2.get())
		self.u = float(self.e3.get())
		if (self.a <= 0) or (self.u < self.l) or (self.l <= 0):
			print ("ERROR: Bounded pareto paramater error")
			self.errorMessage.set("Bounded pareto paramater error")
			return 1
		else:
			self.errorMessage.set("")
			BoundedParetoDist.Array = [self.a, self.l, self.u]
			return 0

		
#----------------------------------------------------------------------#
# Class: Node
#
# This class is used to define the linked list nodes.
#
#----------------------------------------------------------------------#
class Node():
	def __init__(self, job, nextNode = None):
		self.job = job
		self.nextNode = nextNode

#----------------------------------------------------------------------#
# Class: LinkedList
#
# This class is used to make the linked list data structure used to
# store jobs.
#
#----------------------------------------------------------------------#
class LinkedList(object):
	Size = 0
	NumJobArrayByClass = []
	Count = 0

	def __init__(self, head = None):
		self.head = head
		LinkedList.NumJobArrayByClass[:] = []
		LinkedList.Count = 0
		LinkedList.Size = 0

	# Insert job into queue (sorted by class, then name)
	def insertByClass(self, job):
		current = self.head		# node iterator, starts at head
		previous = None
		if (current == None):	# if queue is empty, set current job as head
			self.head = Node(job, None)
		else:
			while (current != None) and (job.priorityClass >= current.job.priorityClass) and (job.name > current.job.name):
				previous = current 				# prev = node[i]
				current = current.nextNode 		# current = node[i+1]
			
			# Insert new node after previous before current
			if (previous == None):
				self.head = Node(job, current)
			else:
				previous.nextNode = Node(job, current)

		LinkedList.Size += 1

	def insertByERPT(self, job, numClasses):
		current = self.head		# node iterator, starts at head
		previous = None
		if (current == None):	# if queue is empty, set current job as head
			self.head = Node(job, None)
		else:
			while (current != None) and (job.priorityClass >= current.job.priorityClass) and (job.ERPT > current.job.ERPT):
				previous = current 				# prev = node[i]
				current = current.nextNode 		# current = node[i+1]
			
			# Insert new node after previous before current
			if (previous == None):
				self.head = Node(job, current)
			else:
				previous.nextNode = Node(job, current)

		LinkedList.Size += 1	

	def insertByLCFS(self, job, numClasses):
		current = self.head		# node iterator, starts at head
		previous = None
		if (current == None):	# if queue is empty, set current job as head
			self.head = Node(job, None)
		else:
			while (current != None) and (current.job.priorityClass != numClasses):			# insert at front of last class
				previous = current 				# prev = node[i]
				current = current.nextNode 		# current = node[i+1]
			
			# Insert new node after previous (before current)
			if (previous == None):
				self.head = Node(job, current)
			else:
				previous.nextNode = Node(job, current)

		LinkedList.Size += 1		

	# Remove first item in queue
	def removeHead(self):
		if (LinkedList.Size > 0):
			self.head = self.head.nextNode		# move head forward one node
			LinkedList.Size -= 1
		else:
			print ("ERROR: The linked list is already empty!")

	def clear(self):
		LinkedList.Size = 0
		self.head = None

	def printList(self):
		current = self.head
		print ("---------------------")
		print ("\nJOBS IN QUEUE:")
		while (current != None):
			print ("%s, class %s, ERPT = %.4f"%(current.job.name, current.job.priorityClass, current.job.ERPT))
			current = current.nextNode


	def countClassesQueued(self, numClasses):
		if(LinkedList.Count == 0):
			LinkedList.NumJobArrayByClass = [0] * (numClasses + 1)	# create array that holds number of jobs in each classes

		# Iterate through number of classes and count number of jobs per class
		for j in range(1, numClasses + 1):
			current = self.head
			while (current != None):
				if current.job.priorityClass == j:
					LinkedList.NumJobArrayByClass[j] += 1
				elif current.job.priorityClass > numClasses:
					LinkedList.NumJobArrayByClass[numClasses] += 1
				current = current.nextNode
		return LinkedList.NumJobArrayByClass


#----------------------------------------------------------------------#
# Class: JobClass
#
# This class is used to define jobs.
#
# Attributes: arrival time, processing time, remaining processing 
# time, estimated remaining processing time, percent error
#----------------------------------------------------------------------#
class JobClass(object):
	BPArray = []
	ArrRate = 0
	
	def __init__(self, master):
		self.master = master
		self.arrivalTime = 0
		self.procTime = 0
		self.RPT = 0		# Real Remaining Processing Time
		self.ERPT = 0		# Estimated Remaining Processing Time
		self.priorityClass = 100
		self.percentError = 0
		self.processRate = 0
		self.arrivalRate = 0

	def setArrProcRates(self, load, procRate, procDist):
		if procDist == 'Bounded Pareto':
			alpha = JobClass.BPArray[0]
			L = JobClass.BPArray[1]
			U = JobClass.BPArray[2]
			if alpha > 1 and L > 0:
				procMean = (L**alpha/(1 - (L/U)**alpha))*(alpha/(alpha - 1))*((1/(L**(alpha - 1)))-(1/(U**(alpha - 1))))
				self.processRate = 1/float(procMean)
		else:
			self.processRate = procRate
		self.arrivalRate = float(load) * self.processRate
		return self.arrivalRate

	# Dictionary of service distributions
	def setServiceDist(self, procRate, procDist):
		ServiceDistributions =  {
			'Poisson': random.expovariate(1.0/procRate),
			'Exponential': random.expovariate(procRate),
			'Uniform': random.uniform(0.0, procRate),
			'Bounded Pareto': self.setBoundedPareto,			
			'Custom': self.setCustomDist
		}
		if(procDist == 'Custom'):
			return ServiceDistributions[procDist](procRate)
		elif(procDist == 'Bounded Pareto'):
			return ServiceDistributions[procDist]()
		else:
			return ServiceDistributions[procDist]

	def setCustomDist(self, procRate):
		if main.timesClicked == 0:
			main.timesClicked += 1
			self.popup=CustomDist(self.master)
			self.master.wait_window(self.popup.top)
			main.customEquation = self.popup.stringEquation
		return eval(main.customEquation)

	def setBoundedPareto(self):
		# Get and set parameters (in job class array)
		if main.timesClicked == 0:
			main.timesClicked += 1
			self.popup = BoundedParetoDist(self.master)
			self.master.wait_window(self.popup.top)		
			self.alpha = float(self.popup.paramArray[0])	# Shape, power of tail, alpha = 2 is approx Expon., alpha = 1 gives higher variance
			self.L = float(self.popup.paramArray[1])		# Smallest job size
			self.U = float(self.popup.paramArray[2])		# Largest job size
			JobClass.BPArray = [self.alpha, self.L, self.U]

			GUI.writeToConsole(self.master, "Alpha = %s \nLower Bound = %s \nUpper Bound = %s" %(self.alpha, self.L, self.U))
			GUI.writeToConsole(self.master, "----------------------------------------------------------------------\n\n")	

		x = random.uniform(0.0, 1.0)
		# reassigning 
		alpha = JobClass.BPArray[0]
		L = JobClass.BPArray[1]
		U = JobClass.BPArray[2]

		#GUI.writeToConsole(self.master, "Alpha = %s \nLower Bound = %s \nUpper Bound = %s" %(alpha, L, U))

		paretoNumerator = float(-(x*(U**alpha) - x*(L**alpha) - (U**alpha)))
		paretoDenominator = float((U**alpha) * (L**alpha))
		main.customEquation = (paretoNumerator/paretoDenominator)**(-1/alpha)
		
		return main.customEquation

	# Generates a percent error for processing time
	def generateError(self, percErrorMin, percErrorMax):
		self.percentError = random.uniform(percErrorMin, percErrorMax)
		return self.percentError

	# Sets all processing times for job
	def setJobAttributes(self, load, procRate, procDist, percErrorMin, percErrorMax, jobArrival):
		if(procDist == 'Bounded Pareto'):
			self.procTime = self.setServiceDist(procRate, procDist) 		#use updated proc rate
			JobClass.ArrRate = self.setArrProcRates(load, procRate, procDist)
		else:
			JobClass.ArrRate = self.setArrProcRates(load, procRate, procDist)
			self.procTime = self.setServiceDist(procRate, procDist) 		#use updated proc rate
		self.estimatedProcTime = (1 + (self.generateError(percErrorMin, percErrorMax)/100.0))*self.procTime
		self.RPT = self.procTime
		self.ERPT = self.estimatedProcTime
		self.arrivalTime = jobArrival


#----------------------------------------------------------------------#
# Class: MachineClass
#
# This class is used to generate Jobs at random and process them.
#
# Entities: jobs, server
# Events: job arrives, job completes
# Activities: processing job, waiting for new job
#
#----------------------------------------------------------------------#
class MachineClass(object):
	Queue = LinkedList()
	PreviousJobs = []
	LastClassPrevJobs = []
	JobOrderOut = []
	CurrentTime = 0.0
	NextArrival = 0.0
	ServiceStartTime = 0
	ServiceFinishTime = 0
	ServerBusy = False
	JobInService = None
	StopSim = False	

	PrevTime = 0
	PrevTimeA = 0
	PrevNumJobs = 0
	AvgNumJobs = 0
	PrevNumJobsArray = []
	AvgNumJobsArray = []
	TotalNumJobsArray = []
	TotalServiceTimesArray = []
	counter = 0


	def __init__(self, master):
		self.master = master
		MachineClass.Queue.clear()
		MachineClass.PreviousJobs[:] = []
		MachineClass.LastClassPrevJobs[:] = []
		MachineClass.CurrentTime = 0.0
		MachineClass.NextArrival = 0.0
		MachineClass.ServiceStartTime = 0
		MachineClass.ServiceFinishTime = 0
		MachineClass.ServerBusy = False
		MachineClass.JobInService = None
		MachineClass.StopSim = False


		MachineClass.PrevTime = 0
		MachineClass.PrevTimeA = 0
		MachineClass.PrevNumJobs = 0
		MachineClass.AvgNumJobs = 0		
		MachineClass.PrevNumJobsArray[:] = []
		MachineClass.AvgNumJobsArray[:] = []
		MachineClass.TotalNumJobsArray[:] = []
		MachineClass.TotalServiceTimesArray[:] = []
		MachineClass.counter = 0

		NumJobs[:] = []
		AvgNumJobs[:] = []
		NumJobsTime[:] = []
		MachineClass.JobOrderOut[:] = []
	
		self.ctr = 0

	# Dictionary of arrival distributions
	def setArrivalDist(self, arrRate, arrDist):
		ArrivalDistributions = {
			'Poisson': random.expovariate(1.0/arrRate),
			'Exponential': random.expovariate(arrRate)
			#'Normal': Rnd.normalvariate(self.inputInstance.valuesList[0])
			#'Custom':
		}
		return ArrivalDistributions[arrDist]
	
	def getProcessingJob(self):
		currentJob = MachineClass.Queue.head.job
		return currentJob

	#update data
	def updateJob(self):
		currentJob = self.getProcessingJob()
		serviceTime = MachineClass.CurrentTime - MachineClass.ServiceStartTime
		currentJob.RPT -= serviceTime
		currentJob.ERPT -= serviceTime

	# Give arriving job a class and add it to the queue
	def assignClass(self, numClasses, job, prevJobs, counterStart, counter, load):
		# Remove oldest job from previous jobs list if there are too many
		while len(prevJobs) > (numClasses - 1):
			prevJobs.pop(0)

		# Sort previous current job with previous jobs
		self.SortedPrevJobs = []
		self.SortedPrevJobs = list(prevJobs) 	# copy of prev jobs
		self.SortedPrevJobs.append(job)							# append current job (not a copy)
		self.SortedPrevJobs.sort(key=lambda JobClass: JobClass.ERPT)

		iterator = counter
		for j in self.SortedPrevJobs:
			if j.name == job.name:
				job.priorityClass = counterStart + counter
			counter += iterator

		# Add job's service time to the total service time
		MachineClass.TotalServiceTimesArray[job.priorityClass] += job.RPT
		MachineClass.TotalNumJobsArray[job.priorityClass] += 1
		self.calcLoadPerClass(load, numClasses)			

		# If job is in the last class, sort by ERPT
		if (job.priorityClass == numClasses):
			#MachineClass.Queue.insertByERPT(job, numClasses);
			MachineClass.Queue.insertByLCFS(job, numClasses);

		else:
			# Add current job with new class to queue
			MachineClass.Queue.insertByClass(job)			# add job to queue
		
		# Regardless of class, append job to the general prev jobs list
		MachineClass.PreviousJobs.append(job)					# add job to previous jobs queue



		# Print queue
		#MachineClass.Queue.printList()
		


	def calcNumJobs(self, jobID, load):
		self.currentNumJobs = MachineClass.Queue.Size #NOTE: This includes job in service
		self.t = MachineClass.CurrentTime
		self.delta_t = self.t - MachineClass.PrevTime 

		# If one job in system
		if(jobID == 0):
			MachineClass.AvgNumJobs = 1 # First event is always create new job
		# UPDATE 
		else:
			MachineClass.AvgNumJobs = (MachineClass.PrevTime/(self.t))*float(MachineClass.AvgNumJobs) + float(MachineClass.PrevNumJobs)*(float(self.delta_t)/self.t)
			
		# PrevTime becomes "old" t
		MachineClass.PrevTime = self.t 
		# PrevNum jobs becomes current num jobs
		MachineClass.PrevNumJobs = self.currentNumJobs

		NumJobs.append(self.currentNumJobs)				# y axis of plot
		AvgNumJobs.append(MachineClass.AvgNumJobs)		# y axis of plot
		NumJobsTime.append(MachineClass.CurrentTime)	# x axis of plot
		#self.saveNumJobs(load, MachineClass.CurrentTime, self.currentNumJobs)
		#self.saveAvgNumJobs(load, MachineClass.CurrentTime, MachineClass.AvgNumJobs)

	def calcNumJobsPerClass(self, numClasses):
		numJobsArray = list(MachineClass.Queue.countClassesQueued(numClasses))

		self.t = MachineClass.CurrentTime 
		self.delta_t = self.t - MachineClass.PrevTimeA

		for i in range(0, numClasses + 1):
			# If one job in system
			if(MachineClass.counter == 0):
				MachineClass.PrevNumJobsArray = [0] * (numClasses + 1) 		# creates array of size (numClasses + 1) filled with 0s
				MachineClass.AvgNumJobsArray = list(numJobsArray)			# First event is always create new job
				MachineClass.counter = 1
				
			# UPDATE 
			else:
				MachineClass.AvgNumJobsArray[i] = (float(MachineClass.PrevTimeA)/self.t)*float(MachineClass.AvgNumJobsArray[i]) + float(MachineClass.PrevNumJobsArray[i])*(float(self.delta_t)/self.t)
									
		# PrevTime becomes "old" t (set in regular caclulation)
		MachineClass.PrevTimeA = self.t 
		# PrevNum jobs becomes current num jobs
		MachineClass.PrevNumJobsArray = list(numJobsArray)
		


	def calcLoadPerClass(self, load, numClasses):
		# The estimate of P_i would be the total number of jobs of class i that have arrived up to time t, 
		#divided by the total number of jobs that have arrived up to time t
		TotalNumJobs = sum(MachineClass.TotalNumJobsArray)
		#print(str(MachineClass.CurrentTime) + "--------------------")
		#print("totaljobs: " + str(TotalNumJobs))

		ProbClass = [i/float(TotalNumJobs) for i in MachineClass.TotalNumJobsArray]
		#print("ProbClass: " + str(ProbClass))

		# The estimate of the expected service time would be the total service time of jobs of class i
		#that have arrived up to time t, divided by the total number jobs of class i that have arrived up to time t		
		#TotalServiceTimes = sum(MachineClass.TotalServiceTimesArray)
		#print("totalservice: " + str(TotalServiceTimes))

		ExpectedServicePerClass = [0] * (numClasses + 1)
		for i in range(len(MachineClass.TotalServiceTimesArray)):
			# If no jobs have ever been in class i, expected service for class i is 0
			if(MachineClass.TotalNumJobsArray[i] == 0):
				#print("no jobs ever been in class %s yet"%i)
				ExpectedServicePerClass[i] = 0.0;
			else:
				#print("toatl jobs in class %s: %f"%(i, MachineClass.TotalNumJobsArray[i]))
				#print("total service time in class %s: %f"%(i, MachineClass.TotalServiceTimesArray[i]))
				ExpectedServicePerClass[i] = MachineClass.TotalServiceTimesArray[i]/float(MachineClass.TotalNumJobsArray[i])

		#print("Expected Service: " + str(ExpectedServicePerClass))

		percentLoadPerClass = [JobClass.ArrRate * x * y for x,y in zip(ProbClass, ExpectedServicePerClass)]
		#print("arr rate: " + str(JobClass.ArrRate))
		#print("Percent Load: " + str(percentLoadPerClass) + "\n")
		self.saveLoadPerClass(load, MachineClass.CurrentTime, numClasses, percentLoadPerClass)
		

		

	def saveNumJobs(self, load, numJobs, time):
		text = "%f,%f"%(numJobs, time) + "\n"
		scaledLoad = int(load * 100)
		path = "./LoadPerClass/Class_Num_load=%s_alpha=%s_servers=1.txt"%(scaledLoad, JobClass.BPArray[0])
		
		with open(path, "a") as myFile:
			myFile.write(text)
		myFile.close()				

	def saveAvgNumJobs(self, load, avgNumJobs, time):
		text = "%f,%f"%(avgNumJobs, time) + "\n"
		scaledLoad = int(load * 100)
		path = "./LoadPerClass/Class_Avg_load=%s_alpha=%s_servers=1.txt"%(scaledLoad, JobClass.BPArray[0])

		with open(path, "a") as myFile:
			myFile.write(text)
		myFile.close()	

	def saveLoadPerClass(self, load, time, numClasses, avgLoadPerClass):
		text =  str(time) + "," + ','.join(repr(i) for i in avgLoadPerClass) + "\n"
		scaledLoad = int(load * 100)
		path = "./LoadPerClass/Class_LoadPerClass_load=%s_alpha=%s_numClasses=%s_servers=1.txt"%(scaledLoad, JobClass.BPArray[0], numClasses)

		with open(path, "a") as myFile:
			myFile.write(text)
		myFile.close()			

	# Job arriving
	def arrivalEvent(self, load, arrDist, procRate, procDist, numClasses, percErrorMin, percErrorMax):
		if(self.ctr == 0):
			MachineClass.TotalServiceTimesArray = [0] * (numClasses + 1) 
			MachineClass.TotalNumJobsArray =  [0] * (numClasses + 1) 

		J = JobClass(self.master)
		J.setJobAttributes(load, procRate, procDist, percErrorMin, percErrorMax, MachineClass.CurrentTime)
		J.name = "Job%02d"%self.ctr
		self.ctr += 1

		if(MachineClass.Queue.Size > 0):
			self.updateJob()	# update data in queue	
		self.assignClass(numClasses, J, MachineClass.PreviousJobs, 0, 1, load)			# give job a class, and add to queue
		#self.saveArrivals(J)					# save to list of arrivals, for testing

		self.calcNumJobs(self.ctr, load)
		self.calcNumJobsPerClass(numClasses)		

		GUI.writeToConsole(self.master, "%.6f | %s arrived, class = %s, RPT=%s"%(MachineClass.CurrentTime, J.name, J.priorityClass, J.RPT))
		self.processJob()						# process first job in queue

		MachineClass.NextArrival = MachineClass.CurrentTime + self.setArrivalDist(J.arrivalRate, arrDist) # generate next arrival
		

	# Inserts very large job with very small ERPT
	def insertLargeJob(self, counter, procDist, numClasses):
		J = JobClass(self.master)
		J.setJobAttributes(1, 1, procDist, 0, 0, MachineClass.CurrentTime)
		J.name = "JobXXXXX" + str(counter)
		J.RPT = 100000
		J.ERPT = 50000
		self.assignClass(numClasses, J, MachineClass.PreviousJobs, 0, 1)
		GUI.writeToConsole(self.master, "%.6f | %s arrived, ERPT = %.5f"%(MachineClass.CurrentTime, J.name, J.ERPT))
		
		self.calcNumJobs(self.ctr)
		#self.saveArrivals(J)					# save to list of arrivals, for testing
	
		if(MachineClass.Queue.Size > 0):
			self.updateJob()	# update data in queue
		self.processJob()	# process first job in queue
	
		# Generate next arrival
		MachineClass.TimeUntilArrival = self.setArrivalDist(J.arrivalRate, 'Exponential')		

	# Processing first job in queue
	def processJob(self):
		MachineClass.ServiceStartTime = MachineClass.CurrentTime
		MachineClass.JobInService = self.getProcessingJob()
		MachineClass.ServiceFinishTime = MachineClass.CurrentTime + MachineClass.JobInService.RPT
		GUI.writeToConsole(self.master, "%.6f | %s processing, class = %s"%(MachineClass.CurrentTime, MachineClass.JobInService.name, MachineClass.JobInService.priorityClass))
		MachineClass.ServerBusy = True

	# Job completed
	def completionEvent(self, numClasses, load):
		MachineClass.JobOrderOut.append(MachineClass.JobInService.name)

		self.calcNumJobs(self.ctr, load)
		self.calcNumJobsPerClass(numClasses)

		GUI.writeToConsole(self.master, "%.6f | %s COMPLTED"%(MachineClass.CurrentTime, MachineClass.JobInService.name))
		MachineClass.ServerBusy = False
		MachineClass.JobInService = None
		
		MachineClass.Queue.removeHead()		 # remove job from queue		


	def run(self, load, arrDist, procRate, procDist, percErrorMin, percErrorMax, numClasses, simLength):
		counter = 1;
		while 1:
			# Generate time of first job arrival
			if(self.ctr == 0):
				arrRate = float(load) / procRate
				MachineClass.NextArrival = MachineClass.CurrentTime + self.setArrivalDist(arrRate, arrDist)

			if (MachineClass.ServerBusy == False) or ((MachineClass.ServerBusy == True) and (MachineClass.NextArrival < MachineClass.ServiceFinishTime)):
				#next event is arrival
				MachineClass.CurrentTime = MachineClass.NextArrival

				# stop server from processing current job
				MachineClass.ServerBusy == False
				self.arrivalEvent(load, arrDist, procRate, procDist, numClasses, percErrorMin, percErrorMax)
			else:
				#next event is job finishing
				MachineClass.CurrentTime = MachineClass.ServiceFinishTime
				self.completionEvent(numClasses, load)

				if(MachineClass.Queue.Size > 0):
					self.processJob()

			# If current time is greater than the simulation length, end program
			if (MachineClass.CurrentTime > simLength) or (MachineClass.StopSim == True):
				break



#----------------------------------------------------------------------#
def main():
	window = GUI(None)                           			   # instantiate the class with no parent (None)
	window.title('Single Server Approximate SRPT with Errors')  # title the window

	# Global variables used in JobClass
	main.timesClicked = 0       
	main.customEquation = ""

	#window.geometry("500x600")                     # set window size
	window.mainloop()                               # loop indefinitely, wait for events


if __name__ == '__main__': main()
