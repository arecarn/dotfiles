/*==============================================================================
* includes.h - Master Header File
================================================================================
* General type definitions
==============================================================================*/
typedef unsigned char  INT8U;
typedef signed char    INT8S;
typedef unsigned short INT16U;
typedef signed short   INT16S;
typedef unsigned long  INT32U;
typedef signed long    INT32S;

/*==============================================================================
* General Defined Constants
 =============================================================================*/
#define FALSE  0
#define TRUE   1

#define OFF    0
#define ON     1
#define TOGGLE 2

#define BIT0 0x01
#define BIT1 0x02
#define BIT2 0x04
#define BIT3 0x08
#define BIT4 0x10
#define BIT5 0x20
#define BIT6 0x40
#define BIT7 0x80

/*==============================================================================
* General defined macros
 =============================================================================*/
#define FOREVER()           while(1)
#define TRAP()              while(1){}

#define SET_PIN(Port,Bit)   Port |=  Bit
#define CLEAR_PIN(Port,Bit) Port &= ~Bit

#define SIZEOFARRAY(A)  (sizeof A / sizeof *A) //will not work for passed arrays

/*==============================================================================
* MCU specific definitions
 =============================================================================*/

/*==============================================================================
* Project Constant and Macro Definitions
 =============================================================================*/

/*==============================================================================
* System Header Files
 =============================================================================*/

/*==============================================================================
* Module Header Files or Declarations
 =============================================================================*/

