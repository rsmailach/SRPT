#----------------------------------------------------------------------#
# main.py
#
# This application simulates a single server with Poisson arrivals
# and processing times of a general distribution. There are errors in
# time estimates within a range. Arrivals are assigned to SRPT classes
# using the methods described in Adaptive and Scalable Comparison Scheduling.
#
# Rachel Mailach
#----------------------------------------------------------------------#

from SimPy.Simulation import *
from Tkinter import *
from datetime import datetime
from random import seed,Random,expovariate,uniform,normalvariate # https://docs.python.org/2/library/random.html
import ttk


#----------------------------------------------------------------------#
# Class: GUI
#
# This class is used as a graphical user interface for a larger
# application.
#
#----------------------------------------------------------------------#
class GUI(Tk):
	def __init__(self, master):
		Tk.__init__(self, master)

		self.master = master        # reference to parent
		random.seed(datetime.now())

		# create the input frame
		self.frameIn = Input(self)
		self.frameIn.grid(row = 0, column = 0, padx = 5, pady =5, ipadx = 5, ipady = 5)

		# create the output frame
		self.frameOut = Output(self)
		self.frameOut.grid(row = 1, column = 0, padx = 5, pady =5, ipadx = 5, ipady = 5)

		# bind simulate button
		self.bind("<<input_simulate>>", self.submit)

		# initialize console
		self.makeConsole()

	def makeConsole(self):
		self.console = Text(self.frameOut, wrap = WORD)
		self.console.config(state=DISABLED) # start with console as disabled (non-editable)
		scrollbar = Scrollbar(self.frameOut)
		scrollbar.config(command = self.console.yview)
		self.console.config(yscrollcommand=scrollbar.set)
		self.console.grid(column=0, row=0)
		scrollbar.grid(column=1, row=0, sticky='NS')

	def writeToConsole(self, text = ' '):
		self.console.config(state=NORMAL) # make console editable
		self.console.insert(END, '%s\n'%text)
		self.update()
		self.console.config(state=DISABLED) # disable (non-editable) console

	def clearConsole(self):
        #       self.console.config(state=NORMAL) # make console editable
		self.console.delete('1.0', END)
        #       self.console.config(state=DISABLED) # disable (non-editable) console

	def printParams(self, arrRate, procRate, percError, splitMech, simLength):
		self.writeToConsole("\nPARAMETERS:")
		self.writeToConsole("Arrival Rate = %.4f"%arrRate)
		self.writeToConsole("Processing Rate = %.4f"%procRate)
		self.writeToConsole("% Error  = " + u"\u00B1" + " %.4f"%percError)
		self.writeToConsole("Splitting mechanism = %d"%splitMech)
		self.writeToConsole("Simulation Length = %.4f\n"%simLength)

	def DisplayData(self):
		self.writeToConsole('\nSINGLE SERVER SRPT')
		self.writeToConsole('Average number of jobs in the system at any given time %s' %ArrivalClass.m.timeAverage())
		self.writeToConsole('Average time in system, from start to completion is %s' %ArrivalClass.mT.mean())
		self.writeToConsole('Average processing time, based on generated service times is %s' %ArrivalClass.msT.mean())

	def submit(self, event):
		#self.frameOut.GetOutputList()
		#self.clearConsole()
		self.writeToConsole("--------------------------------------------------------------------------------")
		self.writeToConsole("Simulation begun")

		inputInstance = Input(self)
		resource=Resource(capacity=1, name='Processor')

		self.printParams(inputInstance.valuesList[0], inputInstance.valuesList[1],\
				 inputInstance.valuesList[2], inputInstance.valuesList[3],\
				 inputInstance.valuesList[4])

		initialize()
		A = ArrivalClass(self)
		activate(A, A.GenerateArrivals(	inputInstance.valuesList[0], "Exponential",\
						inputInstance.valuesList[1], inputInstance.distList[1],\
						inputInstance.valuesList[2], inputInstance.valuesList[3], resource))

		ArrivalClass.m.observe(0)        # number in system is 0 at the start
		simulate(until=inputInstance.valuesList[4])

		self.DisplayData()
		
		self.writeToConsole("\nSimulation complete")

#----------------------------------------------------------------------#
# Class: NonZeroEntry
#
# This class verifies inputs are non-zero.
#
#----------------------------------------------------------------------#
#class NonZeroEntry(Entry):
#        def __init__(self, master, value="", minValue=None, **kw):
#		self.minValue = minValue
#                apply(ValidatingEntry.__init__, (self, master), kw)

#        def validate(self, value):
#                if self.minValue is None or value > minValue:
#                        return value
#                return None # value is zero!
# http://effbot.org/zone/tkinter-entry-validate.htm

#----------------------------------------------------------------------#
# Class: Input
#
# This class is used as a graphical user interface for a larger
# application.
#
#----------------------------------------------------------------------#
class Input(LabelFrame):
	valuesList = []

	def __init__(self, parent):
		LabelFrame.__init__(self, parent, text = "Input")

		self.arrivalRateInput = DoubleVar()
		self.processingRateInput = DoubleVar()
		self.percentErrorInput = DoubleVar()
		self.splittingMechanismInput = IntVar()
		self.simLengthInput = DoubleVar()

		# create widgets, parent = self because window is parent
		# Labels
		labels = [u'\u03bb', u'\u03bc', '% error            ' u"\u00B1", 'splitting mechansim', 'simulation length']
		r=0
		c=0
		for elem in labels:
			Label(self, text=elem).grid(row=r, column=c)
			r=r+1

		# Entry Boxes
		self.entry_1 = Entry(self, textvariable = self.arrivalRateInput)
		self.entry_2 = Entry(self, textvariable = self.processingRateInput)
		self.entry_3 = Entry(self, textvariable = self.percentErrorInput)
		self.entry_4 = Entry(self, textvariable = self.splittingMechanismInput)
		self.entry_5 = Entry(self, textvariable = self.simLengthInput)

		# Simulate Button
		self.simulateButton = Button(self, text = "SIMULATE", command = self.OnButtonClick)

		self.distributions = ('Select Distribution', 'Exponential', 'Normal', 'Custom')

		#self.comboBox_1 = ttk.Combobox(self, values = self.distributions, state = 'readonly')
		#self.comboBox_1.current(0) # set selection

		self.comboBox_2 = ttk.Combobox(self, values = self.distributions, state = 'readonly')
		self.comboBox_2.current(0) # set selection

		self.entry_1.grid(row = 0, column = 1)
		self.entry_2.grid(row = 1, column = 1)
		self.entry_3.grid(row = 2, column = 1)
		self.entry_4.grid(row = 3, column = 1)
		self.entry_5.grid(row = 4, column = 1)

		self.simulateButton.grid(row = 5, columnspan = 2)

		#self.comboBox_1.grid(row = 0, column = 2)
		self.comboBox_2.grid(row = 1, column = 2)

	def OnButtonClick(self):
		self.GetNumericValues()
		self.GetDropDownValues()

		# send to submit button in main
		self.simulateButton.event_generate("<<input_simulate>>")


	def GetNumericValues(self):
		arrivalRate = self.arrivalRateInput.get()
		processingRate = self.processingRateInput.get()
		percentError = self.percentErrorInput.get()
		splittingMechanism = self.splittingMechanismInput.get()
		maxSimLength = self.simLengthInput.get()

		if arrivalRate <= 0.0: GUI.writeToConsole(self.master, "Arrival rate has to be non-zero!")
		if processingRate <= 0.0: GUI.writeToConsole(self.master, "Processing rate has to be non-zero!")
		#if percentError <= 0.0: GUI.writeToConsole(self.master, "Percent error has to be non-zero!")
		#if splittingMechanism <= 0: GUI.writeToConsole(self.master, "Splitting mechanism has to be non-zero!")
		if maxSimLength <= 0.0: GUI.writeToConsole(self.master, "Simulation length has to be non-zero!")

		Input.valuesList = [arrivalRate, processingRate, percentError, splittingMechanism, maxSimLength]
		return Input.valuesList

	def GetDropDownValues(self):
		#if self.comboBox_1.get() == 'Select Distribution': print "Box 1 has to have a selection"
		if self.comboBox_2.get() == 'Select Distribution': GUI.writeToConsole(self.master, "You must select a distribution for the processing rate")

		Input.distList = ["", self.comboBox_2.get(), "", "", ""]
		return Input.distList

	#def CreateList(self):
	#	InputList = zip(Input.valuesList, Input.distList)
	#	return InputList


#----------------------------------------------------------------------#
# Class: Output
#
# This class is used as a graphical user interface for a larger
# application.
#
#----------------------------------------------------------------------#
class Output(LabelFrame):
	def __init__(self, parent):
		LabelFrame.__init__(self, parent, text = "Output")


#----------------------------------------------------------------------#
# Class: ServerClass
#
# This class is used to actually model the job processing.
#
#----------------------------------------------------------------------#
class ServerClass(Process):
	NumJobsInSys = 0
	CompletedJobs = 0
	Queue = [] 		# jobs queued for the machines

	def __init__(self, master):
		Process.__init__(self)
		self.master = master





	def ExecuteJobs(self, server):
		ServerClass.NumJobsInSys += 1
		ArrivalClass.m.observe(ServerClass.NumJobsInSys)

		GUI.writeToConsole(self.master, "%s requests service                        | %s"%(self.name, now()))
		yield request,self, server
		GUI.writeToConsole(self.master, "%s server request granted, begin executing | %s"%(self.name, now()))
		Job = MachineClass.Queue.pop(0)			# job is no longer in queue, now going to be processed
		


		ArrivalClass.msT.observe(procTime)
		yield hold, self, Job.procTime 

		# job completed, release
		yield release, self, server
		GUI.writeToConsole(self.master, "%s completed                               | %s"%(self.name, now()))
		ServerClass.NumJobsInSys -= 1
		ArrivalClass.m.observe(ServerClass.NumJobsInSys)
		ArrivalClass.mT.observe(now() - Job.arrivalTime)
	
		#GUI.writeToConsole(self.master, "Current number of jobs in the system %s"%JobClass.NumJobsInSys)
		#GUI.writeToConsole(self.master, "\nQUEUE LENGTH: %d"%len(self.server.queue))

#----------------------------------------------------------------------#
# Class: JobClass
#
# This class is used to define jobs.
#
#----------------------------------------------------------------------#
class JobClass(object):
	def __init__(self):
		self.arrivalTime = now()
		self.procTime = 0



	# dictionary of service distributions
	def SetServiceDist(self, procRate, procDist):
		self.ServiceDistributions =  {
			'Exponential': random.expovariate(procRate)
			#'Normal': Rnd.normalvariate(self.ServiceRate)
			#'Custom':
		}
		return self.ServiceDistributions[procDist]

	# generates a percent error for processing time
	def GenerateError(self, percError):
		self.percentError = pow(-1, random.randint(0,1)) * (percError * random.random())
		#GUI.writeToConsole(self.master, "Generated Error: %.4f"%self.percentError)
		return self.percentError

	def SetJobAttributes(self, procRate, procDist, percError):
		# generate processing time for the job
		procTime = self.SetServiceDist(procRate, procDist)
		errorProcTime = (1 + (self.GenerateError(percError)/100.0))*procTime
		self.procTime = errorProcTime

#----------------------------------------------------------------------#
# Class: ArrivalClass
#
# This class is used to generate Jobs at random.
#
#----------------------------------------------------------------------#
class ArrivalClass(Process):
	def __init__(self, master):
		Process.__init__(self)
		self.master = master

		ArrivalClass.m = Monitor() # monitor for number of jobs
		ArrivalClass.mT = Monitor() # monitor for time in system
		ArrivalClass.msT = Monitor() # monitor for generated service times

		# reset monitors 
		ArrivalClass.m.reset()
		ArrivalClass.mT.reset()
		ArrivalClass.msT.reset()	
	
		self.ctr = 0

	# Dictionary of arrival distributions
	def SetArrivalDist(self, arrRate, arrDist):
		ArrivalDistributions = {
			'Exponential': random.expovariate(arrRate)
			#'Normal': Rnd.normalvariate(self.inputInstance.valuesList[0])
			#'Custom':
		}
		return ArrivalDistributions[arrDist]

	def SortQueue(self, splitMech):
		#grab the previous m (splitMech) jobs to sort jobs by processing time (procTime) 
		Server.Queue[-(splitMech+1):] = sorted(Server.Queue[-(splitMech+1):], key=lambda J: J.procTime) 
	
	def GenerateArrivals(self, arrRate, arrDist, procRate, procDist, percError, splitMech, server):
		while 1:
			# wait for arrival of next job
			yield hold, self, self.SetArrivalDist(arrRate, arrDist)

			J = JobClass()
			J.SetJobAttributes(procRate, procDist, percError)
			J.name = "Job%02d"%self.ctr
			
			ServerClass.Queue.append(J) #add job to queue
			GUI.writeToConsole(self.master, "QUEUE LENGTH: %d"%len(ServerClass.Queue))
	
			activate(J, J.ExecuteJobs(server), delay=0)


			self.ctr += 1

			
			



#----------------------------------------------------------------------#
def main():
	window = GUI(None)                          # instantiate the class with no parent (None)
	window.title('Single Server SRPT with Errors')  # title the window
	#window.geometry("500x600")                     # set window size
	window.mainloop()                               # loop indefinitely, wait for events


if __name__ == '__main__': main()
