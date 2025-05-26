import FreeCAD, FreeCADGu
import FreeCAD as App
import FreeCADGui as Gui
import os
from PySide import QtGui

# Path setup
script_dir = os.path.dirname(os.path.abspath(__file__))
ICONPATH = os.path.join(script_dir, "resources")


class SectionImport:

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "icons/Tsec.svg"),
            "Accel": "",
            "MenuText": "Import Section Data",
            "ToolTip": "Import section properties from text file"
        }

    def Activated(self):
        dialog = QtGui.QFileDialog()
        dialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        dialog.setNameFilter("Text Files (*.txt);;All Files (*)")
        dialog.setViewMode(QtGui.QFileDialog.Detail)

        if dialog.exec_():
            filepath = str(dialog.selectedFiles()[0])
        else:
            App.Console.PrintWarning("File selection cancelled.\n")
            return

        if not filepath or not os.path.isfile(filepath):
            App.Console.PrintWarning("Invalid file path selected.\n")
            return

        doc = App.ActiveDocument
        if not doc:
            App.Console.PrintError("No active document found.\n")
            return

        # Create empty parametric object with a dummy shape
        obj = doc.addObject("Part::FeaturePython", "SectionData")
        obj.Label = "SectionData"
        ViewProviderSection(obj.ViewObject) 
        proxy = SectionProxy(obj)

        # Load section properties from file
        SectionProxy.load_section_properties(filepath, obj)

        doc.recompute()

    def IsActive(self):
        return App.ActiveDocument is not None



class ViewProviderSection:
    def __init__(self, obj):
        obj.Proxy = self
    

    def getIcon(self):
        return """/* XPM */
static char * profile_xpm[] = {
"32 32 213 2",
"  	c None",
". 	c #060B17",
"+ 	c #09101D",
"@ 	c #0B1222",
"# 	c #0C1222",
"$ 	c #0C1422",
"% 	c #0D1422",
"& 	c #0D1522",
"* 	c #0E1522",
"= 	c #0F1522",
"- 	c #0F1622",
"; 	c #101622",
"> 	c #101722",
", 	c #111722",
"' 	c #121722",
") 	c #121822",
"! 	c #141822",
"~ 	c #141922",
"{ 	c #151922",
"] 	c #161A22",
"^ 	c #171A22",
"/ 	c #171B22",
"( 	c #14171D",
"_ 	c #101316",
": 	c #08101E",
"< 	c #4075E1",
"[ 	c #4C88FF",
"} 	c #518CFF",
"| 	c #568FFF",
"1 	c #5B92FF",
"2 	c #6095FF",
"3 	c #6599FF",
"4 	c #6A9CFF",
"5 	c #6F9FFF",
"6 	c #73A2FF",
"7 	c #78A6FF",
"8 	c #7DA9FF",
"9 	c #82ACFF",
"0 	c #87AFFF",
"a 	c #8CB3FF",
"b 	c #91B6FF",
"c 	c #95B9FF",
"d 	c #9ABDFF",
"e 	c #9FC0FF",
"f 	c #A4C3FF",
"g 	c #A9C6FF",
"h 	c #97B0DE",
"i 	c #15181E",
"j 	c #070E1E",
"k 	c #3972E1",
"l 	c #4684FF",
"m 	c #4B87FF",
"n 	c #4F8AFF",
"o 	c #548EFF",
"p 	c #5991FF",
"q 	c #5E94FF",
"r 	c #6397FF",
"s 	c #689BFF",
"t 	c #6D9EFF",
"u 	c #72A1FF",
"v 	c #76A4FF",
"w 	c #7BA8FF",
"x 	c #80ABFF",
"y 	c #85AEFF",
"z 	c #8AB1FF",
"A 	c #8FB5FF",
"B 	c #94B8FF",
"C 	c #98BBFF",
"D 	c #9DBFFF",
"E 	c #A2C2FF",
"F 	c #91ACDE",
"G 	c #336DE1",
"H 	c #3F7FFF",
"I 	c #4483FF",
"J 	c #4986FF",
"K 	c #4E89FF",
"L 	c #528CFF",
"M 	c #5790FF",
"N 	c #5C93FF",
"O 	c #6196FF",
"P 	c #6699FF",
"Q 	c #6B9DFF",
"R 	c #70A0FF",
"S 	c #75A3FF",
"T 	c #79A6FF",
"U 	c #7EAAFF",
"V 	c #83ADFF",
"W 	c #88B0FF",
"X 	c #8DB3FF",
"Y 	c #92B7FF",
"Z 	c #97BAFF",
"` 	c #9BBDFF",
" .	c #8BA8DE",
"..	c #14181E",
"+.	c #050E1E",
"@.	c #2D6AE1",
"#.	c #387BFF",
"$.	c #3D7EFF",
"%.	c #4281FF",
"&.	c #4785FF",
"*.	c #518BFF",
"=.	c #558EFF",
"-.	c #5A92FF",
";.	c #5F95FF",
">.	c #6498FF",
",.	c #699BFF",
"'.	c #6E9FFF",
").	c #78A5FF",
"!.	c #7CA8FF",
"~.	c #81ACFF",
"{.	c #86AFFF",
"].	c #8BB2FF",
"^.	c #90B5FF",
"/.	c #86A4DE",
"(.	c #12161E",
"_.	c #050D1E",
":.	c #2865E1",
"<.	c #3276FF",
"[.	c #367AFF",
"}.	c #3B7DFF",
"|.	c #4080FF",
"1.	c #4583FF",
"2.	c #4A87FF",
"3.	c #548DFF",
"4.	c #5890FF",
"5.	c #5D94FF",
"6.	c #6297FF",
"7.	c #679AFF",
"8.	c #6C9DFF",
"9.	c #71A1FF",
"0.	c #7BA7FF",
"a.	c #7FAAFF",
"b.	c #84AEFF",
"c.	c #89B1FF",
"d.	c #8EB4FF",
"e.	c #80A0DE",
"f.	c #030A19",
"g.	c #030B1A",
"h.	c #040C1B",
"i.	c #060C1B",
"j.	c #060D1B",
"k.	c #070D1B",
"l.	c #050A13",
"m.	c #355FB1",
"n.	c #578FFF",
"o.	c #6096FF",
"p.	c #4568AE",
"q.	c #080C13",
"r.	c #0C111B",
"s.	c #0C121B",
"t.	c #0D121B",
"u.	c #0F131B",
"v.	c #0E121A",
"w.	c #0D1219",
"x.	c #2C53A0",
"y.	c #508BFF",
"z.	c #5A91FF",
"A.	c #3A5B9D",
"B.	c #2850A0",
"C.	c #538DFF",
"D.	c #36599D",
"E.	c #244DA0",
"F.	c #4282FF",
"G.	c #32569D",
"H.	c #1F4BA0",
"I.	c #377AFF",
"J.	c #3C7DFF",
"K.	c #4584FF",
"L.	c #2E539D",
"M.	c #1B48A0",
"N.	c #3075FF",
"O.	c #3579FF",
"P.	c #3A7CFF",
"Q.	c #29509D",
"R.	c #1745A0",
"S.	c #2971FF",
"T.	c #2E74FF",
"U.	c #3377FF",
"V.	c #264E9D",
"W.	c #1342A0",
"X.	c #236CFF",
"Y.	c #2770FF",
"Z.	c #2C73FF",
"`.	c #3176FF",
" +	c #214A9D",
".+	c #1040A0",
"++	c #1C68FF",
"@+	c #216BFF",
"#+	c #266EFF",
"$+	c #2A72FF",
"%+	c #1D489D",
"&+	c #1966FF",
"*+	c #1A67FF",
"=+	c #1F6AFF",
"-+	c #246DFF",
";+	c #19459D",
">+	c #1D69FF",
",+	c #15429D",
"'+	c #113F9D",
")+	c #0F3F9D",
"!+	c #020A19",
"~+	c #020A1A",
"{+	c #020B1B",
"]+	c #020813",
"^+	c #1147B1",
"/+	c #1146AE",
"(+	c #030C1E",
"_+	c #165AE1",
":+	c #1659DE",
"<+	c #010915",
"[+	c #030C1D",
"}+	c #030D22",
"|+	c #010916",
"        . + @ # $ % & * = - ; > , ' ) ! ~ { { ] ^ / ( _         ",
"        : < [ } | 1 2 3 4 5 6 7 8 9 0 a b c d e f g h i         ",
"        j k l m n o p q r s t u v w x y z A B C D E F i         ",
"        j G H I J K L M N O P Q R S T U V W X Y Z `  ...        ",
"        +.@.#.$.%.&.[ *.=.-.;.>.,.'.6 ).!.~.{.].^.c /.(.        ",
"        _.:.<.[.}.|.1.2.n 3.4.5.6.7.8.9.v 0.a.b.c.d.e.(.        ",
"        f.g.h.i.i.j.k.k.l.m.L n.1 o.p.q.r.r.s.t.t.u.v.w.        ",
"                          .+m y.=.z.A.                          ",
"                          .+I J K C.D.                          ",
"                          .+$.F.&.[ G.                          ",
"                          .+I.J.|.K.L.                          ",
"                          .+N.O.P.H Q.                          ",
"                          .+.S.T.U.#.V.                          ",
"                          .+X.Y.Z.`. +                          ",
"                          .+++@+#+$+%+                          ",
"                          .+&+*+=+-+;+                          ",
"                          .+&+&+&+>+,+                          ",
"                          .+&+&+&+&+'+                          ",
"                          .+&+&+&+&+)+                          ",
"                          .+&+&+&+&+)+                          ",
"                          .+&+&+&+&+)+                          ",
"                          .+&+&+&+&+)+                          ",
"                          .+&+&+&+&+)+                          ",
"                          .+&+&+&+&+)+                          ",
"                          .+&+&+&+&+)+                          ",
"        !+~+{+{+{+{+{+{+]+^+&+&+&+&+/+]+{+{+{+{+{+{+~+!+        ",
"        (+_+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+:+(+        ",
"        (+_+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+:+(+        ",
"        (+_+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+:+(+        ",
"        (+_+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+:+(+        ",
"        (+_+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+&+:+(+        ",
"        <+[+}+}+}+}+}+}+}+}+}+}+}+}+}+}+}+}+}+}+}+}+[+|+        "};
        """





class SectionProxy:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyArea", "AreaSection", "Section", "Section area")
        obj.addProperty("App::PropertyFloat", "MomentInertiaPolar", "Section", "Polar Moment of Inertia")
        obj.addProperty("App::PropertyFloat", "MomentInertiaY", "Section", "Moment of Inertia Y")
        obj.addProperty("App::PropertyFloat", "MomentInertiaZ", "Section", "Moment of Inertia Z")
        obj.addProperty("App::PropertyFloat", "ProductInertiaYZ", "Section", "Product of Inertia")

    @staticmethod
    def load_section_properties(filepath, target_obj):
        try:
            with open(filepath, 'r') as file:
                lines = file.readlines()

            for line in lines:
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # Attempt to convert the value to float
                    try:
                        value = float(value)
                    except ValueError:
                        App.Console.PrintWarning(f"Invalid value for {key}: {value}. Skipping.\n")
                        continue

                    # Set the property if it exists on the target object
                    if hasattr(target_obj, key):
                        setattr(target_obj, key, value)
                        App.Console.PrintMessage(f"Set {key} = {value}\n")
                    else:
                        App.Console.PrintWarning(f"Property {key} not found on object.\n")

        except Exception as e:
            App.Console.PrintError(f"Error reading file: {e}\n")

        App.ActiveDocument.recompute()


# Register the command in FreeCAD
Gui.addCommand("import_section", SectionImport())
