import QtQuick 2.5
import QtQuick.Controls 1.1

Canvas
{
    width: 400;
    height: 400;
    id: robocanvas;

    property real robotX: 0;
    property real robotY: 0;
    property real robotHeading: 0;
    property real robotRadius: 0.25;
    
    property real zoom: 0.2;
    property real centerX: 0.0;
    property real centerY: 0.0;

    property bool seesLine: false;

    property var lines: [];

    onRobotHeadingChanged:
    {
        robocanvas.requestPaint();
    }

    onRobotXChanged:
    {
        robocanvas.requestPaint();
    }

    onRobotYChanged:
    {
        robocanvas.requestPaint();
    }

    function drawBackground(ctx)
    {
        ctx.save()

        ctx.lineWidth = 2 / width;
        ctx.strokeStyle = "gray";
        ctx.beginPath();
        ctx.moveTo(0, -1);
        ctx.lineTo(0, 1);
        ctx.stroke();
        ctx.moveTo(-1, 0);
        ctx.lineTo(1, 0);
        ctx.stroke();
        ctx.restore();
    }

    function drawLines(ctx)
    {
        ctx.save();
        for(var i=0; i<lines.length; i++)
        {
            if(lines[i].style == 0)
            {
                ctx.strokeStyle = "pink";
            }
            else
            {
                ctx.strokeStyle = "black";
            }
            ctx.lineWidth = lines[i].width;
            ctx.beginPath();
            ctx.moveTo(lines[i].beg.x, lines[i].beg.y);
            ctx.lineTo(lines[i].end.x, lines[i].end.y);
            ctx.stroke();
            //todo: draw lines so that there are no holes at the end points
        }
        ctx.restore();
    }

    function drawRobot(ctx, x, y, h)
    {
        ctx.save();
        ctx.translate(robotX, robotY);
        ctx.rotate(robotHeading);
        ctx.scale(robotRadius, robotRadius);

        if (seesLine)
        {
            ctx.fillStyle = "pink";
        }
        else
        {
            ctx.fillStyle = "light blue";
        }
            
        ctx.lineWidth = 2 / width / robotRadius;
        ctx.strokeStyle = "blue";

        ctx.beginPath();
        ctx.rect(-0.75, -1.25, 1.5, 0.5);
        ctx.fill();
        ctx.stroke()

        ctx.beginPath();
        ctx.rect(-0.75, 0.75, 1.5, 0.5);
        ctx.fill();
        ctx.stroke()

        ctx.beginPath();
        ctx.arc(0, 0, 1.0, 0, Math.PI * 2.0, false);
        ctx.fill();
        ctx.stroke()

        ctx.beginPath();
        ctx.moveTo( 0.75, 0 );
        ctx.lineTo( 0.6, 0.15);
        ctx.lineTo( 0.6, -0.15);
        ctx.closePath();
        ctx.fillStyle = "blue";
        ctx.fill();

        ctx.restore();
    }

    onPaint:
    {
        var ctx = getContext("2d");
        ctx.reset();

        ctx.fillStyle = "dark grey";
        ctx.beginPath();
        ctx.rect(0, 0, width, height);
        ctx.fill();
        ctx.save();
        ctx.scale(width, -height);
        ctx.translate(0.5, -0.5);
        ctx.scale(zoom, zoom);
        ctx.translate(-centerX, centerY);

        drawBackground(ctx);
        drawLines(ctx);
        drawRobot(ctx, robotX, robotY, robotHeading);
        ctx.restore();
    }

    MouseArea 
    {
        anchors.fill: parent
        function adjustZoom(zoom)
        {
            robocanvas.zoom += zoom;
            if(robocanvas.zoom < 0.01)
            {
                robocanvas.zoom = 0.01;
            }
            robocanvas.requestPaint();
        }
        onWheel: {

            if (wheel.modifiers & Qt.ControlModifier)
            {
                adjustZoom(wheel.angleDelta.y / 240);
            } 
            else if (wheel.modifiers & Qt.ShiftModifier)
            {
                robocanvas.centerX -= wheel.angleDelta.y / robocanvas.width / robocanvas.zoom * 0.5;
                robocanvas.requestPaint();
            }
            else
            {
                robocanvas.centerX -= wheel.angleDelta.x / robocanvas.width / robocanvas.zoom * 0.5;
                robocanvas.centerY -= wheel.angleDelta.y / robocanvas.height / robocanvas.zoom * 0.5;
                robocanvas.requestPaint();

            }
        }
    }
}