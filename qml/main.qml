import QtQuick 2.5
import QtQuick.Controls 1.1
import QtCharts 2.0

ApplicationWindow {
    id: window
    visible: true
    width: 1000
    height: 600

	Row
	{
		Column
		{
			Row
			{
				CheckBox
				{
					text: "Left bumper"
					checked: robot.left_bumper
				}
				CheckBox
				{
					text: "Right bumper"
					checked: robot.right_bumper
				}
			}

			RoboView
			{
				robotX: robot.x;
				robotY: robot.y;
				robotHeading: robot.heading;			
			}
		}
	}
}

