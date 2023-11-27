import sys
import arrow
import time
import numpy as np
import math

#Graphs libraries
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
from datetime import timedelta, datetime
from matplotlib.path import Path
import seaborn as sns
import itertools
import matplotlib.patches as patches
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from scipy.interpolate import make_interp_spline


class Graph_generator(object):

	def __init__(self,start_date : None,
					  end_date: None,
					  report_type: None):

		self.start_date = start_date
		self.end_date = end_date
		self.complete_dates = [self.start_date.shift(days=i) for i in range((self.end_date - self.start_date).days + 1)]
		self.complete_dates = [a.format('DD-MM') for a in self.complete_dates]
		self.font = {'family': 'Arial'}

		self.report_type = report_type


	def unique_values(self, dates, values):

		# Convert date strings to NumPy datetime64
		x = np.array(dates, dtype='datetime64')
		# Convert values to NumPy array
		y = np.array(values)

		# Get unique dates
		unique_dates = np.unique(x)

		# Calculate average value for each unique date
		averaged_values = []
		for date in unique_dates:
			mask = x == date
			avg_value = np.mean(y[mask])
			averaged_values.append(avg_value)


		# Convert back to NumPy arrays
		x_unique = np.array(unique_dates, dtype='datetime64')
		y_avg = np.array(averaged_values)

		return(x_unique, y_avg)

	def weekly_average(self,x, y):
		#print(x)
		#print(y)
		x_npdate64 = all(isinstance(item, np.datetime64) for item in x)
		if x_npdate64:
			x = [item.astype(datetime) for item in x]

		try:

			x = [datetime.strptime(date.strftime('%Y-%m-%d'), '%Y-%m-%d') for date in x]

			# Create an array of week numbers corresponding to each date
			week_numbers = [date.isocalendar()[1] for date in x]
			#print(week_numbers)
			# Initialize lists to store the weekly averages
			week_avg_dates = []
			week_avg_weights = []

			current_week = week_numbers[0]
			weekly_weight_sum = 0
			weekly_weight_count = 0

			for date, weight, week in zip(x, y, week_numbers):
				if week == current_week:
					weekly_weight_sum += weight
					weekly_weight_count += 1
				else:
					# Append the average for the previous week

					if weekly_weight_count > 0:
						week_avg_dates.append(date + timedelta(days=3))
						week_avg_weights.append(weekly_weight_sum / weekly_weight_count)
					current_week = week
					weekly_weight_sum = weight
					weekly_weight_count = 1

			# Append the last week's average
			if weekly_weight_count > 0:
				week_avg_dates.append(x[-1] + timedelta(days=3))
				week_avg_weights.append(weekly_weight_sum / weekly_weight_count)

			#print(week_avg_dates)
			#print(week_avg_weights)

		except:

			week_avg_dates = []
			week_avg_weights = []


		
		return(week_avg_dates, week_avg_weights)

	def smooth_lines(self,x,y):

		# Convert datetime objects to matplotlib date numbers
		x = mdates.date2num(x)
		y = y

		if len(x) > 3:
			# Interpolate y values using the new x values

			try:
				# Create interpolation function
				interpolation_function = make_interp_spline(x, y)

				# Generate new x values for smooth curve
				new_x = np.linspace(min(x), max(x), num=50)
				smooth_y = interpolation_function(new_x)
				# Convert matplotlib date numbers back to datetime objects
				smooth_dates = mdates.num2date(new_x)

				return(smooth_dates,smooth_y)

			except:
				return(x,y)
		else:
			return(x,y)


	def plot_scatter(self, x, y, k, j, name):


		fig, ax = plt.subplots()

		index_0 = [index for index, value in enumerate(y) if value is None or value == 0]
		index_1 = [index for index, value in enumerate(j) if value is None or value == 0]


		y = [value for value in y if value is not None and value != 0]
		j = [value for value in j if value is not None and value != 0]

		# X is a character to represent the timestamp ( e.g., '16782892902')
		x = [datetime.fromtimestamp(timestamp) for timestamp in x]
		x = [value for index, value in enumerate(x) if index not in index_0]

		#print(k)
		
		# k, start_date and end_date are arroe types (e.g.,  <Arrow [2023-08-27T01:00:00+01:00]>)
		k = [value for index, value in enumerate(k) if index not in index_1]


		plt.clf()

		# Create a scatter plot
		sns.set_style("whitegrid",{ "grid.linewidth":0.5, "grid.color": ".8", "grid.linestyle": ":", "ytick.left": True})


		if y == [] and j == []:

			fig, ax = plt.subplots()

			# Step 3 (Optional): Add labels and titles to the plot
			ax.set_xlabel('Date', fontdict = self.font)
			ax.set_ylabel('Date', fontdict = self.font)

		else:
			#print('**************************************WEEKLY************************************************************')
			# Smooth lines
			date_avg, val_avg = self.weekly_average(k, j)
			#print('**************************************WEEKLY************************************************************')
			k_s,j_s = self.smooth_lines(k,j)

			if self.report_type == 1:
				sns.scatterplot( x= x, y = y, color = "cornflowerblue", label = 'Respiration Rate')
				sns.lineplot(x = k_s, y = j_s, color = "darkblue",label = 'Respiration Rate Average')

				fig_size = fig.get_size_inches()
				#print('FIG SIZE', fig_size)

				for t, t1 in zip(k, j):
					if math.isnan(t1):
						plt.text(t, t1-(0.1* fig_size[1]), math.floor(t1), ha='center', va='center', size = 11.2, color = "black")
						plt.gca().set_xticks([])
					else:
						circle = patches.Ellipse((t, t1), width= 0.045 * fig_size[0], height= 0.3* fig_size[1], facecolor= "white")
						circle.set_zorder(5)
						plt.gca().add_patch(circle)
						plt.text(t, t1-(0.1* fig_size[1]), math.floor(t1), ha='center', va='bottom', size = 11.5, color ="black", zorder=6, fontdict = self.font)				
				plt.gca().set_xlim((self.start_date.replace(hour=0, minute=0, second=0, microsecond=0)).shift(hours = -5), self.end_date)
				plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
				# Set the locator for x-axis labels
				plt.gca().xaxis.set_major_locator(mdates.DayLocator())	
				plt.tick_params(axis = 'x', which = 'major', labelsize = 11)
				try:
					plt.ylim(min(y)-5, max(y)+5)
				except:
					print('Empty data')

			if self.report_type == 0:

				if len(j_s) < 2:
					sns.scatterplot( x= k_s, y = j_s, label = "Respiration Rate", color = "darkblue")
				else:
					max_thresh = np.mean(j_s) + np.std(j_s)
					min_thresh = np.mean(j_s) - np.std(j_s)
					aver_thresh = np.mean(j_s)

					sns.lineplot(x = k_s, y = j_s, color = "darkblue",label = 'Respiration Rate Average')
					# Threshold calculations
					plt.axhline(y=max_thresh, color='darkorange', linestyle='--', label=f'Upper limit: {max_thresh:.2f}', linewidth = 1)
					plt.axhline(y=min_thresh, color='darkorange', linestyle='--', label=f'Lower limit: {min_thresh:.2f}', linewidth = 1)
					plt.axhline(y=aver_thresh, color='mediumseagreen', linestyle='--', label= f'Average: {aver_thresh:.2f}', linewidth = 1)

					plt.tick_params(axis = 'x', which = 'major', labelsize = 11)
					plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
					plt.gca().set_xlim((self.start_date.replace(hour=0, minute=0, second=0, microsecond=0)).shift(hours = -5), self.end_date)

					for index in range(len(date_avg)):

						plt.text(date_avg[index], val_avg[index], math.floor(val_avg[index]), size = 11.5,  rotation = 45, fontdict = self.font, bbox=dict(boxstyle='circle', facecolor='lightblue', edgecolor='white'))

		
			if name == 'RR':

				plt.gca().set_title('Sleep Respiration Rate', fontsize = 14, loc = 'left',pad = 30, fontweight= 600, fontdict = self.font)
				plt.ylabel("Breaths per minute", fontsize = 11, fontdict = self.font)


			elif name == 'HR':
			
				plt.gca().set_title('Sleep Heart Rate', fontsize = 14, loc = 'left',pad = 30, fontweight= 600, fontdict = self.font)
				plt.ylabel("Heart Rate (bpm)", fontsize = 11, fontdict = self.font)
						
			elif name == 'HR_ScanWatch':

				plt.gca().set_title('Daily Heart Rate', fontsize = 14, loc = 'left',pad = 30, fontweight= 600, fontdict = self.font)
				plt.ylabel("Heart Rate (bpm)", fontsize = 11, fontdict = self.font)
			
		
			plt.grid(axis = "x")

			plt.gca().spines['top'].set_visible(False)
			plt.gca().spines['right'].set_visible(False)




		plt.legend(loc= 'upper center', bbox_to_anchor = (0.5,1.09), ncol =2 , frameon=False)
		# Remove the border around the legend box
		
		plt.savefig(name + 'Scatter.png', dpi = 500)

		# Display the plot
		#plt.show()


	def plot_min_max_av(self,x_values,y_average,y_min,y_max,device,type_d):

		x_values = [datetime.fromtimestamp(a.timestamp()) for a in x_values]

		# Calculate the range (difference between min and max)

		y_range = []

		y_average = [float('nan') if element is None else element for element in y_average]
		y_min = [float('nan') if element is None else element for element in y_min]
		y_max = [float('nan') if element is None else element for element in y_max]

		y_average = [float('nan') if x == 0 else x for x in y_average]
		y_min = [float('nan') if x == 0 else x for x in y_min]
		y_max = [float('nan') if x == 0 else x for x in y_max]

		#print('x_values', x_values)
		#print('y_values', y_average)


		x_values1, y_average = self.unique_values(x_values, y_average)
		x_values1, y_min = self.unique_values(x_values, y_min)
		x_values1, y_max = self.unique_values(x_values, y_max)


		plt.clf()

		for i, j, z in zip(y_average,y_min,y_max):

			y_range.append([i-j, z-i])

		y_range = np.transpose(y_range)

		# Create the figure and axis

		sns.set_style("whitegrid",{ "grid.linewidth":0.5, "grid.color": ".8", "grid.linestyle": ":", "ytick.left": True})

		# Plot the average line
		sns.scatterplot(x = x_values1, y = y_average, color='green', label='Heart Rate Average')

		# Plot the error bars (range)
		plt.errorbar(x_values1, y_average, yerr= y_range, fmt='o', color='green', ecolor='mediumseagreen', capsize=5)

		if device == "ScanWatch":

			
			plt.gca().set_title('ScanWatch: Heart Rate',fontsize = 14, loc = 'left',pad = 30, fontweight = 600)

		elif device == "SleepMat" and type_d == "HR":
			
			plt.gca().set_title('SleepMat: Heart Rate',fontsize = 14, loc = 'left',pad = 30, fontweight = 600, fontdict = self.font)

		elif device == "SleepMat" and type_d == "RR":
			
			plt.gca().set_title('SleepMat: Respiration Rate',fontsize = 14, loc = 'left',pad = 30, fontweight = 600, fontdict = self.font)

		# Add legend
		plt.legend(loc= 'upper center', bbox_to_anchor = (0.5,1.09), ncol =2)
		# Remove the border around the legend box
		plt.legend().set_frame_on(False)

		# Set the x-axis format as dates
		plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
		# Set the locator for x-axis labels
		plt.gca().xaxis.set_major_locator(mdates.DayLocator())


		# Add average value as text
		for x, y in zip(x_values1, y_average):
			if math.isnan(y):
				plt.text(x, y, y, ha='center', va='bottom', size = 11.5, fontdict = self.font)
			else:
				plt.text(x, y, math.floor(y), ha='center', va='bottom', size = 11.5, fontdict = self.font)


		# Show the plot
		#plt.savefig('my_plot.png')
		plt.gca().yaxis.set_label_coords(-0.1,0.5)
		plt.tick_params(axis = 'x', which = 'major', labelsize = 11)
		plt.grid(axis = "x")
		# Remove the top and right spines
		plt.gca().spines['top'].set_visible(False)
		plt.gca().spines['right'].set_visible(False)
		plt.savefig(device+"_"+type_d, dpi = 500)

		#plt.show()

	def plot_continous(self,date_weight, weight, date_muscle_mass, muscle_mass, date_bone_mass,
							bone_mass, date_fat_mass, fat_mass, date_hydration, hydration, st_date, ed_date, device):

		# Create a scatter plot
		sns.set_style("whitegrid",{ "grid.linewidth":0.5, "grid.color": ".8", "grid.linestyle": ":", "ytick.left": True})

		
		st_date = st_date.format("D - MMM")
		ed_date = ed_date.format("D - MMM")

		index_0 = [index for index, value in enumerate(weight) if value is None or value == 0 or math.isnan(value)]
		index_1 = [index for index, value in enumerate(muscle_mass) if value is None or value == 0 or math.isnan(value)]
		index_2 = [index for index, value in enumerate(bone_mass) if value is None or value == 0 or math.isnan(value)]
		index_3 = [index for index, value in enumerate(fat_mass) if value is None or value == 0 or math.isnan(value)]
		index_4 = [index for index, value in enumerate(hydration) if value is None or value == 0 or math.isnan(value)]

		#x = [datetime.fromtimestamp(a.timestamp()) for a in x]
		#print(x)
		weight = [value for value in weight if value is not None and value != 0 and not math.isnan(value)]
		muscle_mass = [value for value in muscle_mass if value is not None and value != 0 and not math.isnan(value)]
		bone_mass = [value for value in bone_mass if value is not None and value != 0 and not math.isnan(value)]
		fat_mass = [value for value in fat_mass if value is not None and value != 0 and not math.isnan(value)]
		hydration = [value for value in hydration if value is not None and value != 0 and not math.isnan(value)]
		
		date_weight = [value for index, value in enumerate(date_weight) if index not in index_0]
		date_muscle_mass = [value for index, value in enumerate(date_muscle_mass) if index not in index_1]
		date_bone_mass = [value for index, value in enumerate(date_bone_mass) if index not in index_2]
		date_fat_mass = [value for index, value in enumerate(date_fat_mass) if index not in index_3]
		date_hydration = [value for index, value in enumerate(date_hydration) if index not in index_4]

		weight_date_avg, weight_avg = self.weekly_average(date_weight, weight)
		mm_date_avg , mm_avg = self.weekly_average(date_muscle_mass, muscle_mass)
		bm_date_avg, bm_avg = self.weekly_average(date_bone_mass, bone_mass)
		fm_date_avg, fm_avg = self.weekly_average(date_fat_mass, fat_mass)
		hydration_date_avg, hydration_avg = self.weekly_average(date_hydration, hydration)




		date_strings = [dt.strftime('%Y-%m-%d') for dt in weight_date_avg]

		# Smooth lines
		x_s,y_s = self.smooth_lines(date_weight,weight)
		#y_s = [round(elem) for elem in y_s]
		x_s2,z_s = self.smooth_lines(date_muscle_mass,muscle_mass)
		x_s3,w_s = self.smooth_lines(date_bone_mass,bone_mass)
		x_s4,t_s = self.smooth_lines(date_fat_mass,fat_mass)
		x_s5,l_s = self.smooth_lines(date_hydration,hydration)

		

		max_thresh = np.mean(y_s) + np.std(y_s)
		min_thresh = np.mean(y_s) - np.std(y_s)
		aver_thresh = np.mean(y_s)


		plt.clf()

		plt.gca().set_xticks(weight)

		if device == "Scale":

			# Create a scatter plot
			sns.set_style("whitegrid",{ "grid.linewidth":0.5, "grid.color": ".8", "grid.linestyle": ":", "ytick.left": True})
			
			if len(weight_avg) < 2:
				sns.scatterplot( x= weight_date_avg, y = weight_avg, label = "Weight", color = "darkblue")
			else:
				sns.lineplot(x = x_s, y = y_s, label = "Weight", color = "darkblue", linestyle='-', linewidth = 2)
				# Threshold calculations
				plt.axhline(y=max_thresh, color='darkorange', linestyle='--', label=f'Upper limit: {max_thresh:.2f}', linewidth = 1)
				plt.axhline(y=min_thresh, color='darkorange', linestyle='--', label=f'Lower limit: {min_thresh:.2f}', linewidth = 1)
				plt.axhline(y=aver_thresh, color='mediumseagreen', linestyle='--', label= f'Average: {aver_thresh:.2f}', linewidth = 1)

			#sns.lineplot(x = x_s2, y = z_s, label = "Muscle mass", linestyle='--',  color = "mediumseagreen", linewidth = 2)
			#sns.lineplot(x = x_s3, y = w_s, label = "Bone mass",linestyle='--',  color = "yellow", linewidth = 2)
			#sns.lineplot(x = x_s4, y = t_s, label = "Fat mass", linestyle='--', color = "mediumpurple", linewidth = 2)
			#sns.lineplot(x = x_s5, y = l_s, label = "Hydration (%)", linestyle='--', color = "cornflowerblue", linewidth = 2)
			# Set x-axis tick locations and labels

			# Make specific ticks transparent or not display them
			plt.gca().set_xticks([])

			for index in range(len(weight_date_avg)):

				plt.text(weight_date_avg[index], weight_avg[index], math.floor(weight_avg[index]), size = 11.5,  rotation = 45, fontdict = self.font, bbox=dict(boxstyle='circle', facecolor='lightblue', edgecolor='white'))

			#for index in range(len(mm_date_avg)):
				#plt.text(mm_date_avg[index], mm_avg[index], math.floor(mm_avg[index]), size = 11.5,  rotation = 45, fontdict = self.font)
				#plt.text(bm_date_avg[index], bm_avg[index], math.floor(bm_avg[index]), size = 11.5,  rotation = 45, fontdict = self.font)
				#plt.text(fm_date_avg[index], fm_avg[index], math.floor(fm_avg[index]), size = 11.5,  rotation = 45, fontdict = self.font)
				#plt.text(hydration_date_avg[index], hydration_avg[index], math.floor(hydration_avg[index]), size = 11.5,  rotation = 45, fontdict = self.font)



			if len(z_s) == 0:
				plt.ylim(min(y_s)-0.5, max(y_s)+0.5)

			plt.gca().set_title('Weight',fontsize = 14, loc = 'left',pad = 30, fontweight= 600, fontdict = self.font)
			plt.ylabel("kg", fontdict = self.font)
			plt.xlabel(st_date +" to "+ ed_date)
			plt.legend(loc= 'upper center', bbox_to_anchor = (0.5,1.09), ncol = 4, fontsize = 8.5,frameon=False)
			# Setting y-axis ticks to integer values
			plt.yticks(range(int(min(y_s))-1, int(max(y_s))+3))
			#plt.ylim(min(y_s)-1, max(y_s)+1)

			# Set the x-axis format as dates

			#plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
		
			plt.tick_params(axis = 'x', which = 'major', labelsize = 11)
			plt.gca().spines['top'].set_visible(False)
			plt.gca().spines['right'].set_visible(False)

			# Display the plot
		
			plt.grid(axis = "x")


		plt.savefig(device, dpi = 500)
		#plt.show()

	def plot_bar(self,x,y):

		# Create a scatter plot
		sns.set_style("whitegrid",{ "grid.linewidth":0.5, "grid.color": ".8", "grid.linestyle": ":", "ytick.left": True})

		check = np.array(y)
		if (y == [] or (np.all(check == 0))):


			# Step 3 (Optional): Add labels and titles to the plot
			plt.ylabel('Hours', fontsize = 11, fontdict = self.font)
			plt.xlabel('Dates', fontsize = 11, fontdict = self.font)
			plt.grid(axis = "x")
			plt.gca().set_xticks([])
			plt.gca().set_title('Steps', fontsize = 14, loc = 'left',pad = 30, fontweight=600, fontdict = self.font)

		else:

			x = [datetime.fromtimestamp(a.timestamp()) for a in x]

			y = [0 if element is None else element for element in y]

			x, y = self.unique_values(x,y)



			plt.clf()

			plt.gca().set_title('Daily Steps Count',fontsize = 14, loc = 'left',pad = 30, fontweight= 600, fontdict = self.font)
			plt.grid(axis = "x")
			plt.gca().spines['top'].set_visible(False)
			plt.gca().spines['right'].set_visible(False)
			plt.legend( loc='upper center', bbox_to_anchor=(0.5,1.09), ncol = 3, frameon=False)

			if self.report_type == 1:
				
				# Create a bar plot

				plt.bar(x, y, color = 'lightgreen', label = "Steps", width = 0.4)
				plt.tick_params(axis = 'x', which = 'major', labelsize = 11)

				plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
				# Set the locator for x-axis labels
			
				plt.gca().set_ylim(0, max(y[~np.isnan(y)])+250)
				plt.gca().xaxis.set_major_locator(mdates.DayLocator())
				plt.gca().set_xlim((self.start_date.replace(hour=0, minute=0, second=0, microsecond=0)).shift(hours = -5), self.end_date)

				

			if self.report_type == 0:

				date_avg, val_avg = self.weekly_average(x, y)

				if len(y) < 2:
						sns.scatterplot( x= x, y = y, label = "Steps", color = "darkblue")
				else:
					max_thresh = np.mean(y) + np.std(y)
					min_thresh = np.mean(y) - np.std(y)
					aver_thresh = np.mean(y)

					sns.lineplot(x = x, y = y, color = "darkblue",label = "Steps")
					# Threshold calculations
					plt.axhline(y=max_thresh, color='darkorange', linestyle='--', label=f'Upper limit: {max_thresh:.2f}', linewidth = 1)
					plt.axhline(y=min_thresh, color='darkorange', linestyle='--', label=f'Lower limit: {min_thresh:.2f}', linewidth = 1)
					plt.axhline(y=aver_thresh, color='mediumseagreen', linestyle='--', label= f'Average: {aver_thresh:.2f}', linewidth = 1)

					plt.tick_params(axis = 'x', which = 'major', labelsize = 11)
					plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
					plt.gca().set_xlim((self.start_date.replace(hour=0, minute=0, second=0, microsecond=0)).shift(hours = -5), self.end_date)

					for index in range(len(date_avg)):

						plt.text(date_avg[index], val_avg[index], math.floor(val_avg[index]), size = 11.5,  rotation = 45, fontdict = self.font, bbox=dict(boxstyle='circle', facecolor='lightblue', edgecolor='white'))






		#plt.grid(axis = "x")
		
		plt.savefig('Steps_curvedbar', dpi = 500)

		# Display the plot
		#plt.show()

	def plot_stacked_bar(self,x,y,z,o):

		# Create a scatter plot
		sns.set_style("whitegrid",{ "grid.linewidth":0.5, "grid.color": ".8", "grid.linestyle": ":", "ytick.left": True})

		# Create a figure and axes

		check = np.array(y)
		check1 = np.array(z)
		check2 = np.array(o)


		if (y == [] or (np.all(check == 0))) and (z == [] or (np.all(check1 == 0))) and (o == [] or (np.all(check2 == 0))):


			# Step 3 (Optional): Add labels and titles to the plot
			plt.ylabel('Hours', fontsize = 11, fontdict = self.font)
			plt.xlabel('Dates', fontsize = 11, fontdict = self.font)
			plt.grid(axis = "x")
			plt.gca().set_xticks([])
			plt.gca().set_title('Sleep Summary', fontsize = 14, loc = 'left',pad = 30, fontweight=600, fontdict = self.font)

		else:

			x1 = x
			#start_date = [arrow_datetime.datetime for arrow_datetime in start_date]
			#end_date = [arrow_datetime.datetime for arrow_datetime in end_date]

			#print('x from this', x)

			#y = [x/3600 for x in y]
			#z = [x/3600 for x in z]

			x_u = x1
			o_u = o

			#x_u, l_u = self.unique_values(x,l)


			x_soft, o_soft= self.smooth_lines(x_u,o_u)
			#x_soft, l_soft = self.smooth_lines(x_u,l_u)

			plt.clf()

			plt.bar(x1, y, label='Hours Asleep', color = "cornflowerblue")
			plt.bar(x1, z, label='Hours Awake in bed', bottom = y, color = "lightblue")


			sns.lineplot(x = x_soft, y = o_soft, color = "darkblue", markersize = 14, label = "Times out of bed", zorder = 9, linewidth = 2 )
			#sns.lineplot(x = x_soft, y = l_soft, color = "darkgreen", markersize = 14, label = "Times woken up in bed" , zorder = 9, linewidth = 2)


			for index in range(len(x_u)):
				# Draw the circle patch
				circle = patches.Ellipse((x_u[index], o_u[index]), width= 0.35, height= 0.65, facecolor= "lavender")
				plt.gca().add_patch(circle)
				#circle1 = patches.Ellipse((x_u[index], l_u[index]), width= 0.35, height= 0.65, facecolor= "honeydew")
				circle.set_zorder(10)
				#circle1.set_zorder(10)
				#plt.gca().add_patch(circle1)
				plt.text(x_u[index], o_u[index], math.floor(o_u[index]), size = 11.5, color = "black", ha = 'center', va = 'center', zorder = 11,fontdict = self.font )
				#plt.text(x_u[index], l_u[index], math.floor(l_u[index]), size = 11.5, color = "black", ha = 'center', va = 'center', zorder = 11 )

			# Add labels, title, and legend
			#print(max(y+z))
			plt.grid(axis = "x")
			plt.ylim(bottom = -1)
			plt.ylim(top= (max(y+z)+5))
			plt.tick_params(axis = 'x', which = 'major', labelsize = 11)
			plt.ylabel('Hours', fontsize = 11, fontdict = self.font)
			plt.gca().set_title('Sleep Summary', fontsize = 14, loc = 'left',pad = 30, fontweight=600, fontdict = self.font)
			plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
			plt.gca().set_xlim((self.start_date.replace(hour=0, minute=0, second=0, microsecond=0)).shift(hours = -5), self.end_date)
			# Set the locator for x-axis labels
			plt.gca().spines['top'].set_visible(False)
			plt.gca().spines['right'].set_visible(False)
			#plt.gca().xaxis.set_major_locator(mdates.DayLocator())
			plt.legend(loc= 'upper center', bbox_to_anchor = (0.5,1.09), ncol =3, fontsize = 8.5, frameon=False)

		plt.savefig('sleep_summary', dpi = 500)

		# Show the chart
		#plt.show()


	def plot_events(self,start_times, end_times, amplitudes):

		# Create a figure and axis
		fig, ax = plt.subplots()


		rect2 = []

		#print(start_times)


		# x_limit calculation
		x_lim_min = min(start_times)
		#print('Min date', x_lim_min)
		x_lim_max = max(end_times)
		#print('Min date', x_lim_max)


		legend_handles = {}

		# Loop through each event and plot the colored rectangle

		for start_time, end_time, amplitude in zip(start_times, end_times, amplitudes):

			# Convert start and end times to datetime objects
			start_datetime = start_time.datetime
			start_datetime = mdates.date2num(start_datetime)

			#print(start_datetime)

			end_datetime = end_time.datetime
			end_datetime = mdates.date2num(end_datetime)
			#print(end_datetime)

			# Calculate the duration of the event in minutes (as an integer)
			width = end_datetime - start_datetime

			
			# Create a rectangle patch for the event
			#print(amplitude)
			if amplitude == 1:

				color = 'blue'
				label = 'Light Sleep'

			elif amplitude == 2:
				color = 'cyan'
				label = 'Deep Sleep'
			elif amplitude == 3:
				color = 'gray'
				label = 'REM Sleep'
			else:
				color = 'white'
				label = 'Awake'



			rect = Rectangle((start_datetime, 0), width, amplitude, color = color)

			if label not in legend_handles:
				legend_handles[label] = rect

			# Add the rectangle to the plot
			ax.add_patch(rect)



		locator = mdates.AutoDateLocator(minticks = 3)
		formatter = mdates.DateFormatter(fmt = "%m-%d %H:%M" )

		ax.xaxis.set_major_locator(locator)
		ax.xaxis.set_major_formatter(formatter)

		ax.set_xlim(mdates.date2num(x_lim_min.datetime), mdates.date2num(x_lim_max.datetime))
		ax.set_ylim(0, 4)


		ax.set_ylabel('State', rotation = 0, fontdict = self.font)
		ax.set_title('Sleep states', fontsize = 18, fontdict = self.font)
		
		handles = list(legend_handles.values())
		labels = list(legend_handles.keys())

		ax.spines['top'].set_visible(False)
		ax.spines['right'].set_visible(False)

		# Display the plot
		plt.legend(handles= handles, labels = labels, loc = "upper right", frameon=False)
		plt.show()