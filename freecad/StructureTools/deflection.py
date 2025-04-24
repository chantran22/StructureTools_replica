import FreeCAD, FreeCADGui, Part, math, os
from PySide import QtWidgets

ICONPATH = os.path.join(os.path.dirname(__file__), "resources")
pathFont = os.path.join(os.path.dirname(__file__), "resources/fonts/ARIAL.TTF")
# pathFont = os.path.join(os.path.dirname(__file__), "ARIAL.TTF")

def show_error_message(msg):
	msg_box = QtWidgets.QMessageBox()
	msg_box.setIcon(QtWidgets.QMessageBox.Critical)  #Ícone de erro
	msg_box.setWindowTitle("Erro")
	msg_box.setText(msg)
	msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
	msg_box.exec_()

class Deflection:
	def __init__(self, obj, objCalc, listSelection):
		#Gera a lista de membros selecionados
		


		obj.Proxy = self
		obj.addProperty("App::PropertyLink", "ObjectBaseCalc", "Base", "elementos para a analise").ObjectBaseCalc = objCalc
		obj.addProperty("App::PropertyLinkSubList", "ObjectBaseElements", "Base", "elementos para a analise").ObjectBaseElements = self.getMembers(listSelection)
		

		obj.addProperty("App::PropertyColor", "Color", "Diagram", "elementos para a analise").Color = (150,150,0,0)
		obj.addProperty("App::PropertyInteger", "Transparency", "Diagram", "elementos para a analise").Transparency = 70		
		obj.addProperty("App::PropertyInteger", "FontHeight", "Diagram", "Tamanho da fonte no diagrama").FontHeight = 100
		obj.addProperty("App::PropertyInteger", "Precision", "Diagram", "precisão de casas decimais").Precision = 2
		obj.addProperty("App::PropertyBool", "DrawText", "Diagram", "precisão de casas decimais").DrawText = True

		obj.addProperty("App::PropertyBool", "DeflectionZ", "ResultDeflection", "Show Z-direction deflection").DeflectionZ = False
		obj.addProperty("App::PropertyBool", "DeflectionY", "ResultDeflection", "Show Y-direction deflection").DeflectionY = False
		obj.addProperty("App::PropertyFloat", "ScaleDefl", "ResultDeflection", "Deflection diagram scale").ScaleDefl = 2



	


	# Pega os membros que deverão se plotados os seus diagramas
	def getMembers(self, listSelection):
		listMembers = []

		if listSelection != []: # Caso exista selecção de membros
			for selection in listSelection:
				member = (selection.Object, selection.SubElementNames)
				listMembers.append(member)
		
		else: #Caso não exista seleção de membros todos eles serão selecionados automaticamente
			objects = FreeCAD.ActiveDocument.Objects
			lines = list(filter(lambda object: 'Wire' in object.Name or 'Line' in object.Name, objects))
			members = list(filter(lambda line: 'MaterialMember' in line.PropertiesList, lines))

			for member in members:
				listSubObjects = [f'Edge{i+1}' for i in range(len(member.Shape.Edges))]
				listMembers.append((member, listSubObjects))
		
		return listMembers

	# Gera uma matriz baseado em umdos parâmetros do calc
	def getMatrix(self, param):
		matriz = []
		for linha in param:
			lista = [float(value) for value in linha.split(',')]
			matriz.append(lista)
		
		return matriz


	#  Mapeia os nós da estrutura
	def mapNodes(self, elements):	
		# Varre todos os elementos de linha e adiciona seus vertices à tabela de nodes
		listNodes = []
		for element in elements:
			for edge in element.Shape.Edges:
				for vertex in edge.Vertexes:
					node = [round(vertex.Point.x, 2), round(vertex.Point.y, 2), round(vertex.Point.z, 2)]
					if not node in listNodes:
						listNodes.append(node)

		return listNodes


	# Mapeia os membros da estrutura
	def mapMembers(self, elements, listNodes):
		listMembers = {}
		for element in elements:
			for i, edge in enumerate(element.Shape.Edges):
				listIndexVertex = []
				for vertex in edge.Vertexes:
					node = [round(vertex.Point.x, 2), round(vertex.Point.y, 2), round(vertex.Point.z, 2)]
					index = listNodes.index(node)
					listIndexVertex.append(index)
				# valida se o primeiro nó é mais auto do que o segundo nó, se sim inverte os nós do membro (necessário para manter os diagramas voltados para a posição correta)
				n1 = listIndexVertex[0]
				n2 = listIndexVertex[1]
				if listNodes[n1][2] > listNodes[n2][2]:
					aux = n1
					n1 = n2
					n2 = aux
				listMembers[element.Name + '_' + str(i)] = {
					'nodes': [str(n1), str(n2)],
					'RotationSection': element.RotationSection.getValueAs('rad')
				}
		
		return listMembers
	
	# separa as ordenadas em grupos de valores positivos e negativos
	def separatesOrdinates(self, values):
		loops = []
		loop = [values[0]]
		for i in range(1, len(values)):
			if values[i] * values[i-1] < 0 and abs(values[i]) > 1e-2: #valida  se o valor passa pelo eixo das abssisas comparado com o valor anterior
				loops.append(loop)
				loop = [values[i]]
			else:
				loop.append(values[i])
		
		loops.append(loop)
		
		return loops


	# Função que cria os pares de coordenadas e já cria os valores que cruzam o eixo das absissas
	def generateCoordinates(self, ordinates, dist):
		cont = 0
		loops = []
		loop = []
		for i in range(len(ordinates)):
			for j in range(len(ordinates[i])):
				
				if j == 0 and abs(ordinates[i][j]) > 1e-2 and len(loop) == 0: #Valida se o primeiro valor do loop é maior do que 0
					loop.append([0,0])  

				coordinate = [cont * dist, ordinates[i][j]]
				loop.append(coordinate)
				cont += 1
			
			loops.append(loop)
			loop = []
			if i == len(ordinates) - 1: #valida se foi o ultimo loop a ser processado
				if abs(loops[-1][-1][1]) > 1e-2: #Valida se o valor do ultimo loop é diferente de 0
					loops[-1].append([(cont - 1) * dist,0])
			
			else:
				# calcula o ponto de intersecção com o eixo das abcissas
				o = loops[-1][-1][0]
				a = abs(loops[-1][-1][1])
				b = abs(ordinates[i+1][0])
				x = (a * dist) / (a + b)
				loops[-1].append([o + x, 0]) #Acrecenta o ponto de intersecção no ultimo loop
				loop.append([o + x, 0]) # Acrescenta o ponto de intersecção no inicio do proximo loop
		
		return loops
	

	# Gera as faces
	def generateFaces(self, loops):
		faces = []
		for loop in loops:
			
			loop.append(loop[0])
			loop = [FreeCAD.Vector(value[0], 0, value[1]) for value in loop]

			edges = [Part.LineSegment(loop[i], loop[i+1]).toShape() for i in range(len(loop)-1)]
			wire = Part.Wire(edges)
			face = Part.Face(wire)
			# Valida a face
			if face.Area > 0:
				faces.append(face)
		
		return faces
	
	# Faz a rotação do  diagrama na direção passada como argumento e o posiciona
	def rotate(self, element, dirStart, dirEnd, position = FreeCAD.Vector(0,0,0.1)):
		try:
			dirStart.normalize()
			dirEnd.normalize()

			if dirStart == dirEnd:
				return element.translate(position)       
			
			rotacao = FreeCAD.Rotation(dirStart, dirEnd)
			elementoRotacionado = element.transformGeometry(FreeCAD.Placement(position,rotacao).toMatrix())
			return elementoRotacionado
		except:
			print('Erro ao rotacionar diagrama.')
			return element
	
	# Gero os valores nos diagramas
	def makeText(self, values, listMatrix, dist, fontHeight, precision):
		listWire = []
		for i, value in enumerate(values):
			offset = 0
			valueString = listMatrix[i] * -1
			string = f"{valueString:.{precision}e}"
			x = dist * i
			y = value + offset if value > 0 else value - offset

			text = Part.makeWireString(string, pathFont, fontHeight)
			for wires in text:
				for wire in wires:
					wire = wire.rotated(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), 90)
					wire = wire.translate(FreeCAD.Vector(x, 0, y))
					listWire += [wire]
		
		return listWire


	# Gera o diagrama da matriz passada como argumento
	def makeDiagram(self, matrix,nodes, members, orderMembers, nPoints, rotacao, escale, fontHeight, precision, drawText):
		
		# e = 1e-11
		listDiagram = []
		for i, nameMember in orderMembers:
			p1 = nodes[int(members[nameMember]['nodes'][0])]
			p2 = nodes[int(members[nameMember]['nodes'][1])]
			length = ((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 + (p2[2] - p1[2])**2)**0.5
			dist = length / (nPoints -1) #Distancia entre os pontos no eixo X
			values = [value * escale for value in matrix[i]]

			ordinates = self.separatesOrdinates(values)
			coordinates = self.generateCoordinates(ordinates, dist)
			faces = self.generateFaces(coordinates)
			texts = self.makeText(values, matrix[i], dist, fontHeight, precision)
			
			# Posiciona o diagrama
			dx = p2[0] - p1[0]
			dy = p2[1] - p1[1]
			dz = p2[2] - p1[2]
			element = Part.makeCompound(faces)
			if drawText: element = Part.makeCompound([element] + texts) 

			rot = FreeCAD.Rotation(FreeCAD.Vector(1,0,0), rotacao)
			element.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,0), rot)
			element = self.rotate(element, FreeCAD.Vector(1,0,0), FreeCAD.Vector(abs(dx), abs(dy), abs(dz)))

			if dx < 0 :
				element = element.mirror(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0))
			
			if dy < 0 :
				element = element.mirror(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,1,0))

			
			element = element.translate(FreeCAD.Vector(p1[0], p1[1], p1[2]))
			
			listDiagram.append(element)
			# Part.show(element)
			# Part.show(Part.makeCompound(faces))
			# for face in faces:
			#     Part.show(Part.makeCompound(faces))
		
		return listDiagram

	def filterMembersSelected(self, obj):
		if obj.ObjectBaseElements == []: # se não existir objetos celecionados retorna to d a alista de objetos
			return list(enumerate(obj.ObjectBaseCalc.NameMembers))
		
		else: # caso haja objetos celecionados faz o filtro no nome destes objetos
			listaNames = []
			for element in obj.ObjectBaseElements:
				listMemberNames = [int(name.split('Edge')[1])-1 for name in element[1]]
				for memberName in listMemberNames:
					name = element[0].Name +'_'+ str(memberName)
					memberIndex = obj.ObjectBaseCalc.NameMembers.index(name)
					listaNames.append((memberIndex, name))
			
			return listaNames





	def execute(self, obj):
		elements = list(filter(lambda element: 'Line' in element.Name or 'Wire' in element.Name,  obj.ObjectBaseCalc.ListElements))
		nodes = self.mapNodes(elements)
		members = self.mapMembers(elements, nodes)
		orderMembers = self.filterMembersSelected(obj)

		listDiagram = []
		if obj.DeflectionZ:
			listDiagram += self.makeDiagram(self.getMatrix(obj.ObjectBaseCalc.DeflectionZ), nodes, members, orderMembers, obj.ObjectBaseCalc.NumPointsDeflection, 0, obj.ScaleDefl, obj.FontHeight, obj.Precision, obj.DrawText)
		if obj.DeflectionY:
			listDiagram += self.makeDiagram(self.getMatrix(obj.ObjectBaseCalc.DeflectionY), nodes, members, orderMembers, obj.ObjectBaseCalc.NumPointsDeflection, 0, obj.ScaleDefl, obj.FontHeight, obj.Precision, obj.DrawText)
		
		
		
		if not listDiagram:
			shape = Part.Shape()
		else:	
			shape = Part.makeCompound(listDiagram)

		obj.Shape = shape

		# Estilização
		obj.ViewObject.LineWidth = 1
		obj.ViewObject.PointSize = 1
		obj.ViewObject.LineColor = (int(obj.Color[0]*255),int(obj.Color[1]*255),int(obj.Color[2]*255))
		obj.ViewObject.PointColor = (int(obj.Color[0]*255),int(obj.Color[1]*255),int(obj.Color[2]*255))
		obj.ViewObject.ShapeAppearance = (FreeCAD.Material(DiffuseColor=obj.Color,AmbientColor=(0.33,0.33,0.33),SpecularColor=(0.53,0.53,0.53),EmissiveColor=(0.00,0.00,0.00),Shininess=(0.90),Transparency=(0.00),))
		obj.ViewObject.Transparency = obj.Transparency



	def onChanged(self,obj,Parameter):
		if Parameter == 'edgeLength':
			self.execute(obj)




class CommandDeform():

	def GetResources(self):
		return {"Pixmap"  : os.path.join(ICONPATH, "icons/defl1.svg"), # the name of a svg file available in the resources
				"Accel"   : "", # a default shortcut (optional)
				"MenuText": "Deflection",
				"ToolTip" : "show deflection on member structure"}
	
	def Activated(self):
		objCalc = FreeCADGui.Selection.getSelectionEx()[0].Object
		listSelects = list(filter(lambda select: 'Wire' in select.Object.Name or 'Line' in select.Object.Name, FreeCADGui.Selection.getSelectionEx()))
		
		if 'Calc' in objCalc.Name: #valida se o primeiro elemento de fato é um calc

			doc = FreeCAD.ActiveDocument
			obj = doc.addObject("Part::FeaturePython", "Deflection")
			Deflection(obj, objCalc, listSelects)
			#ViewProviderDiagram(obj.ViewObject) 

		else:
			show_error_message('Deve ser selecionado um objeto calc para traçar o diagrama')
			print('Select calc  object to show deflection')
	
	def IsActive(self):
		return True


FreeCADGui.addCommand("deflection", CommandDeform())