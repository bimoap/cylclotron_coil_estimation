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
