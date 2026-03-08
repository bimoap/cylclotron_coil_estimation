import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pint

# Initialize pint registry
u = pint.get_application_registry()

st.set_page_config(page_title="Coil Estimates", layout="wide")
st.title("Electromagnet Coil & Projectile Estimator")

# --- SIDEBAR INPUTS ---
st.sidebar.header("Input Parameters")

awg = st.sidebar.number_input("Wire AWG", min_value=1, max_value=40, value=28, step=1)
V_val = st.sidebar.number_input("Voltage (V)", value=12.0)
a_val = st.sidebar.number_input("Inner Radius 'a' (mm)", value=12.5)
L_val = st.sidebar.number_input("Solenoid Length 'L' (mm)", value=20.0)
f_val = st.sidebar.number_input("Packing Factor 'f'", value=0.6, max_value=1.0)
j_val = st.sidebar.number_input("Current Density (A/mm²)", value=4.0)
r_ball_val = st.sidebar.number_input("Iron Ball Radius (mm)", value=6.0)
z0_val = st.sidebar.number_input("Switch Position z_0 (mm)", value=-12.0)

# --- APPLY UNITS ---
V = V_val * u.V
a = a_val * u.mm
L = L_val * u.mm
f = f_val
j = j_val * u.A / u.mm**2
r_ball = r_ball_val * u.mm
z_0 = z0_val * u.mm

rho = 1.68e-8 * u.ohm * u.m  # copper resistivity
rho_cu = 8.96 * u.g / u.cm**3
rho_iron = 7874 * u.kg / u.m**3

def awg_diameter(n):
    """Calculate wire diameter from AWG number."""
    return 0.127 * u.mm * 92 ** ((36 - n) / 39)

d_wire = awg_diameter(awg)
A_w = np.pi * (d_wire / 2) ** 2

# Calculate outer radius b
b = np.sqrt(a**2 + (V * A_w) / (j * rho * f * np.pi * L))

# --- DERIVED QUANTITIES ---
l_bar = np.pi * (a + b)
N = V / (j * rho * l_bar)
I = j * A_w
total_length = N * l_bar
P = (I * V).to(u.W)
m_wire = rho_cu * A_w * l_bar * N

st.header("1. Coil Geometry & Derived Quantities")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Wire Diameter", f"{d_wire.to(u.mm).magnitude:.3f} mm")
col2.metric("Conductor Area", f"{A_w.to(u.mm**2).magnitude:.4f} mm²")
col3.metric("Outer Radius (b)", f"{b.to(u.mm).magnitude:.2f} mm")
col4.metric("Radial Build", f"{(b - a).to(u.mm).magnitude:.2f} mm")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Mean Turn Length", f"{l_bar.to(u.mm).magnitude:.1f} mm")
col2.metric("Number of Turns", f"{N.to(u.dimensionless).magnitude:.0f}")
col3.metric("Wire Length", f"{total_length.to(u.m).magnitude:.0f} m")
col4.metric("Wire Mass", f"{m_wire.to(u.g).magnitude:.0f} g")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Current", f"{I.to(u.A).magnitude:.3f} A")
col2.metric("Power", f"{P.magnitude:.1f} W")


# --- BALL & MAGNETIC FIELD ---
def log_mean(a, b):
    return (b - a) / np.log(b / a)

def B_z(z, R, L, N, I):
    """On-axis magnetic field of a finite solenoid."""
    mu_0 = 4 * np.pi * 1e-7 * u.H / u.m
    z_plus = z + L / 2
    z_minus = z - L / 2
    term_plus = z_plus / np.sqrt(R**2 + z_plus**2)
    term_minus = z_minus / np.sqrt(R**2 + z_minus**2)
    return (mu_0 * N / L * I / 2) * (term_plus - term_minus)

def dBz_dz(z, R, L, N, I):
    """Derivative of on-axis field with respect to z."""
    mu_0 = 4 * np.pi * 1e-7 * u.H / u.m
    z_plus = z + L / 2
    z_minus = z - L / 2
    term_plus = R**2 / (R**2 + z_plus**2)**1.5
    term_minus = R**2 / (R**2 + z_minus**2)**1.5
    return (mu_0 * N / L * I / 2) * (term_plus - term_minus)

def F_z(z, R, L, N, I, r_ball):
    """Axial force on an iron sphere (mu_r >> 1)."""
    mu_0 = 4 * np.pi * 1e-7 * u.H / u.m
    V_ball = (4 / 3) * np.pi * r_ball**3
    B = B_z(z, R, L, N, I)
    dB = dBz_dz(z, R, L, N, I)
    return (3 * V_ball / (2 * mu_0)) * B * dB

def work_on_ball(z_0, r_ball, R, L, N, I):
    """Work done on iron ball when field switches on at z_0 - r_ball and off at z_0 + r_ball."""
    mu_0 = 4 * np.pi * 1e-7 * u.H / u.m
    V_ball = (4 / 3) * np.pi * r_ball**3
    z1 = z_0 - r_ball  # field turns on
    z2 = z_0 + r_ball  # field turns off
    B1 = B_z(z1, R, L, N, I)
    B2 = B_z(z2, R, L, N, I)
    return (3 * V_ball / (4 * mu_0)) * (B2**2 - B1**2)

R_eff = log_mean(a, b)
V_ball = (4 / 3) * np.pi * r_ball**3
m_ball = rho_iron * V_ball
v_0 = 0 * u.mm / u.s

B_0 = B_z(0*u.mm, R_eff, L, N, I)
B_on = B_z(z_0 - r_ball, R_eff, L, N, I)
B_off = B_z(z_0 + r_ball, R_eff, L, N, I)

W = work_on_ball(z_0, r_ball, R_eff, L, N, I)
KE_0 = 0.5 * m_ball * v_0**2
KE_f = KE_0 + W
v_f = np.sqrt(2 * KE_f / m_ball)

st.header("2. Iron Ball & Switch Configuration")
col1, col2, col3 = st.columns(3)
col1.metric("Ball Volume", f"{V_ball.to(u.mm**3).magnitude:.0f} mm³")
col2.metric("Ball Mass", f"{m_ball.to(u.g).magnitude:.2f} g")
col3.metric("B at Center", f"{B_0.to(u.mT).magnitude:.1f} mT")

col1, col2, col3 = st.columns(3)
col1.metric("Field ON at z", f"{(z_0 - r_ball).to(u.mm).magnitude:.1f} mm")
col2.metric("Field OFF at z", f"{(z_0 + r_ball).to(u.mm).magnitude:.1f} mm")
col3.metric("Work done on ball", f"{W.to(u.mJ).magnitude:.2f} mJ")

col1, col2, col3 = st.columns(3)
col1.metric("Initial Velocity", f"{v_0.to(u.mm/u.s).magnitude:.0f} mm/s")
col2.metric("Final Velocity", f"{v_f.to(u.mm/u.s).magnitude:.0f} mm/s")
col3.metric("Final Velocity (km/h)", f"{v_f.to(u.km/u.h).magnitude:.2f} km/h")


# --- INDUCTANCE ---
def nagaoka_coefficient(R, L):
    """Nagaoka coefficient for finite solenoid."""
    k = 2 * R / L 
    K = 1 / (1 + 0.9 * R / L - 0.02 * (R / L)**2 + 0.01 * (R / L)**3)
    return K.to(u.dimensionless).magnitude

def solenoid_inductance(N, R, L):
    """Inductance of a finite solenoid."""
    mu_0 = 4 * np.pi * 1e-7 * u.H / u.m
    K = nagaoka_coefficient(R, L)
    return mu_0 * N**2 * np.pi * R**2 * K / L

R_coil = rho * total_length / A_w
L_coil = solenoid_inductance(N, R_eff, L)
tau = L_coil / R_coil
t_on = (2 * r_ball / v_f).to(u.ms)

st.header("3. Inductance & Time Constant")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Nagaoka Coeff (K)", f"{nagaoka_coefficient(R_eff, L):.2f}")
col2.metric("Resistance", f"{R_coil.to(u.ohm).magnitude:.1f} Ω")
col3.metric("Inductance", f"{L_coil.to(u.mH).magnitude:.1f} mH")
col4.metric("Time Constant (τ)", f"{tau.to(u.ms).magnitude:.1f} ms")
st.write(f"**Estimated ON time:** {t_on.magnitude:.4f} ms")


# --- PLOTTING ---
st.header("4. Field and Force Profiles")

# Generate range from -2L to +2L for z-axis
z_vals = np.linspace(-L_val*2, L_val*2, 200) * u.mm

# Calculate B_z and F_z over the z range
B_vals = B_z(z_vals, R_eff, L, N, I).to(u.mT).magnitude
F_vals = F_z(z_vals, R_eff, L, N, I, r_ball).to(u.mN).magnitude

fig, ax1 = plt.subplots(figsize=(10, 5))

# Plot B_z
ax1.set_xlabel('Position z (mm)')
ax1.set_ylabel('Magnetic Field B_z (mT)', color='tab:blue')
ax1.plot(z_vals.magnitude, B_vals, color='tab:blue', label='B_z')
ax1.tick_params(axis='y', labelcolor='tab:blue')
ax1.grid(True, alpha=0.3)

# Indicate the Switch ON/OFF region
z_on_mag = (z_0 - r_ball).to(u.mm).magnitude
z_off_mag = (z_0 + r_ball).to(u.mm).magnitude
ax1.axvspan(z_on_mag, z_off_mag, color='orange', alpha=0.2, label='Coil ON Region (Work Integration)')

# Plot F_z on a secondary y-axis
ax2 = ax1.twinx()
ax2.set_ylabel('Axial Force F_z (mN)', color='tab:red')
ax2.plot(z_vals.magnitude, F_vals, color='tab:red', linestyle='--', label='F_z')
ax2.tick_params(axis='y', labelcolor='tab:red')

fig.legend(loc='upper right', bbox_to_anchor=(0.9, 0.9), bbox_transform=ax1.transAxes)
fig.tight_layout()

# Render plot in Streamlit
st.pyplot(fig)


# --- Solenoid cross-section plot ---
st.header("5. Solenoid Cross-Section")

import matplotlib as mpl

fig2, ax3 = plt.subplots(figsize=(8, 5))

L_mm = L.to(u.mm).magnitude
a_mm = a.to(u.mm).magnitude
b_mm = b.to(u.mm).magnitude
r_ball_mm = r_ball.to(u.mm).magnitude
z_0_mm = z_0.to(u.mm).magnitude

# Calculate switch positions for the plot
z_on = (z_0 - r_ball).to(u.mm).magnitude
z_off = (z_0 + r_ball).to(u.mm).magnitude

# Upper coil cross-section
coil_upper = mpl.patches.Rectangle(
    (-L_mm / 2, a_mm),
    L_mm,
    b_mm - a_mm,
    facecolor='orange',
    edgecolor='black',
    linewidth=1.5,
    label='Coil'
)
ax3.add_patch(coil_upper)

# Lower coil cross-section (mirror)
coil_lower = mpl.patches.Rectangle(
    (-L_mm / 2, -b_mm),
    L_mm,
    b_mm - a_mm,
    facecolor='orange',
    edgecolor='black',
    linewidth=1.5
)
ax3.add_patch(coil_lower)

# Iron ball at switch position
ball = mpl.patches.Circle(
    (z_0_mm, 0),
    r_ball_mm,
    facecolor='gray',
    edgecolor='black',
    linewidth=1.5,
    label='Iron ball'
)
ax3.add_patch(ball)

# Mark switch positions
ax3.axvline(z_on, color='g', linestyle='--', label='Field on')
ax3.axvline(z_off, color='r', linestyle='--', label='Field off')
ax3.axvline(z_0.m_as(u.mm), color='k', linestyle=':', label='Sensor')

# Axis line
ax3.axhline(0, color='k', linestyle='-', linewidth=0.5)

ax3.set_xlim(-50, 50)
ax3.set_ylim(-30, 30)
ax3.set_aspect('equal')
ax3.set_xlabel('z (mm)')
ax3.set_ylabel('r (mm)')
ax3.legend(loc='upper right')
ax3.grid(True, alpha=0.3)
ax3.set_title('Solenoid cross-section (to scale)')

fig2.tight_layout()

# Render in Streamlit instead of plt.show()
st.pyplot(fig2)
