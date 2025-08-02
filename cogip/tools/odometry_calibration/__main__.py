#!/usr/bin/env python3
"""
CLI Script for robot control with user information collection
Uses asyncio for asynchronous input handling
"""

import asyncio
import sys
from typing import Optional

class OdometryCalibration:
    """
    Odometry Calibration
    Determines accurate odometry parameters through calibrated robot movements:

    Wheels distance: Robot rotates in place to measure distance between wheels
    Right Wheel Radius: Square trajectories to calibrate right wheel radius
    Left Wheel Radius: Straight line movement over known distance to calibrate left wheel radius

    Critical Requirements:

    Manually reposition robot to theoretical position after each step (eliminates slippage)
    Provide approximate initial parameter values to start calibration
    Execute steps in order - do not modify sequence

    Note: Final accuracy depends on precise manual repositioning between steps.
    """
    def __init__(self):
        # Trajectories parameters
        self.turns = 0
        self.squares = 0
        self.distance_mm = 0
        
        # Robot parameters
        self.wheels_distance = 0
        self.right_wheel_radius = 0
        self.left_wheel_radius = 0
    
    async def get_user_input(self, prompt: str) -> str:
        """Asynchronous method to get user input"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input, prompt)
    
    async def get_integer_input(self, prompt: str) -> int:
        """Asynchronous method to get integer input with validation"""
        while True:
            try:
                user_input = await self.get_user_input(prompt)
                value = int(user_input)
                
                # Ask for confirmation
                confirm = await self.get_user_input(f"You entered: {value}. Is this correct? (y/n): ")
                if confirm.lower() in ['y', 'yes', '']:
                    return value
                else:
                    print("🔄 Let's try again...")
                    continue
                    
            except ValueError:
                print("❌ Please enter a valid integer.")
                continue
    
    async def wait_for_alignment(self, message: str) -> None:
        """Waits for robot alignment confirmation"""
        await self.get_user_input(f"🤖 {message}")
        print("✅ Alignment confirmed")
    
    async def wait_for_sequence_start(self, message: str) -> None:
        """Waits for sequence start confirmation"""
        await self.get_user_input(f"🚀 {message}")
        print("✅ Sequence started")

    async def wheel_distance_calibration(self) -> None:
        """Phase 1: Robot rotates in place to refine distance between wheels"""
        print("\n" + "="*70)
        print("📍 WHEEL DISTANCE: TURN IN PLACE")
        print("ℹ️ The robot will rotates in place to refine distance between wheels")
        print("="*70)
        
        # Initial alignment
        await self.wait_for_alignment("Please align the robot, then press enter...")
        
        # Number of turns
        self.turns = await self.get_integer_input("🔄 How many turns?\n")
        print(f"📊 Number of turns configured: {self.turns}")
        
        # TODO: CW and CCW choice
        
        # TODO: get current theta
        # Get current encoder counter
        
        # move the robot and wait for the end
        
        # Launch sequence
        await self.wait_for_sequence_start("Press enter to start sequence...")
        
        # Realignment
        await self.wait_for_alignment("Please realign the robot to its initial position and orientation, then press enter...")

    async def right_wheel_radius_calibration(self) -> None:
        """Phase 2: Square trajectories to calibrate right wheel radius"""
        print("\n" + "="*70)
        print("📐 RIGHT WHEEL RADIUS: SQUARES TRAJECTORIES")
        print("ℹ️ The robot will move in square to refine right wheel radius")
        print("="*70)
        
        # New alignment
        await self.wait_for_alignment("Please align the robot, then press enter...")
        
        # Number of squares
        self.squares = await self.get_integer_input("⬜ How many squares?\n")
        print(f"📊 Number of squares configured: {self.squares}")
        
        #TODO: CW and CCW choice
        
        # Launch sequence
        await self.wait_for_sequence_start("Press enter to start sequence...")
        
        # Realignment
        await self.wait_for_alignment("Please realign the robot to its initial position and orientation, then press enter...")
    
    async def left_wheel_radius_calibration(self) -> None:
        """Phase 3: Straight line movement over known distance to calibrate left wheel radius"""
        print("\n" + "="*70)
        print("📏 LEFT WHEEL RADIUS: STRAIGHT LINE")
        print("ℹ️ The robot will move in straight line to refine left wheel radius")
        print("="*70)
        
        # New alignment
        await self.wait_for_alignment("Please align the robot again:")
        
        # Distance in mm
        self.distance_mm = await self.get_integer_input("📐 What distance (in mm)?\n")
        print(f"📊 Distance configured: {self.distance_mm} mm")
        
        # Launch sequence
        await self.wait_for_sequence_start("Press enter to start sequence...")
        
        # Realignment
        await self.wait_for_alignment("Please realign the robot to its initial position and orientation, then press enter...")
    
    async def display_parameters(self, message: str) -> None:
        """Displays a configuration parameters"""
        print("\n" + "="*70)
        print(f"📋 {message}")
        print("="*70)
        print(f"Wheel distance: {self.wheels_distance} mm")
        print(f"Squares completed: {self.right_wheel_radius} mm")
        print(f"Distance traveled: {self.left_wheel_radius} mm")
        print("="*70)
    
    async def run(self) -> None:
        """Main method that executes all phases"""
        try:
            print("🤖 ODOMETRY CALIBRATION TOOL")
            print("Press Ctrl+C to quit at any time\n")
            
            # Display initial parameters
            await self.display_parameters("INITIAL PARAMETERS")
            
            # Sequential execution of phases
            await self.wheel_distance_calibration()
            await self.right_wheel_radius_calibration()
            await self.left_wheel_radius_calibration()
            
            # Display final parameters
            await self.display_parameters("FINAL PARAMETERS")
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Session interrupted by user")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            sys.exit(1)


async def main():
    """Main asynchronous function"""
    controller = OdometryCalibration()
    await controller.run()


if __name__ == "__main__":
    # Python version check
    if sys.version_info < (3, 7):
        print("❌ This script requires Python 3.7 or higher")
        sys.exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Program interrupted")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)