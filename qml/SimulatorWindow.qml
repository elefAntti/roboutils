import QtQuick 2.5
import QtQuick.Controls 1.1

ApplicationWindow {
    id: window
    visible: true
    width: 600
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
					onClicked: robot.left_bumper = checked;
				}
				CheckBox
				{
					text: "Line sensor"
					onClicked: robot.line_sensor = checked;
				}
				CheckBox
				{
					text: "Right bumper"
					onClicked: robot.right_bumper = checked;
				}
			}

			RoboView
			{
				robotX: robot.x;
				robotY: robot.y;
				robotHeading: robot.heading;
				lines: world.lines;
				seesLine: robot.line_sensor;
			}
		}
	}
}

