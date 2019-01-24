# SwapCurves Object

This class provides the user an Object which has the abilites of working on a Swap Curve.
Below you have a brief description of valid functions.
For any question, feel free to contact the developers (@VFermat & @ldunphy98).
For any code suggestion, please reffer to FinanceHub documentation.

## Main Features

### Initialization

When initializing the class, you will need three arguments:

* Rates
  * A Pandas Dataframe containing the SwapCurve data
* Convention
  * A String representing which calendar convention you are using (more on this below)
* Calendar
  * A String representing which days are holidays on your calendar (more on this below)

#### Convention

Valid Conventions:

* `calendar_days` - Year has 360 days
* `business_days` - Year has 252 days

#### Calendar

Valid Calendars:
For now, only Anbima calendar is valid. More to come!

### Functions

#### Plot 3D

Whit this function you are able to plot the surface of a Swap Curve.
Changing `plot_type` parameter to 'wireframe' changes the graphic to a Wire Frame.

Example:

```python
sc.plot_3d()
```

#### Get Rate

With this function you are able to get a Swap Rate for an specific maturity. Even if the title isn`t traded for that maturity.

Parameters:

* base_curve (Array of Datetime objects)
  * These are the dates from which you want to extract the Swap Rate
* desired_terms (Array of maturities in DU)
  * THese are the maturities from which you want to know the Swap Rate
* interpolate_methods (Array of strings containing which Interpolation Methods will be used)
  * Valid Methods:
    * Linear
    * Cubic
    * Quadratic
    * Nearest
    * Flat Forward

#### Get Forward Historic

With this function you are able to view the historic of a Forward Rate between two maturities.

Parameters:

* Maturity 1 (int)
  * Int representing the lowest maturity
* Maturity 2 (int)
  * Int representing the highest maturity
* Plot (Boolean)
  * Boolean that says if the storic should be plotted as well or not
* Interpolate Method (String)
  * String that tells the code which Interpolation Method will be used. (valid methods are the same as in Get Rate)

#### Plot Day Curve

With this function you are able to see the Swap Curve for an specific date (or a set of dates)

Parameters:

* Dates (Array of Datetime objects)
* Interpolate (Boolean)
* Interpolate Methods (Array of strings containing which Interpolation Methods will be used)
* Scatter (Boolean)
